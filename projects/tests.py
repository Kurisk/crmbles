from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
import tempfile

from accounts.models import Business, BusinessMembership, UserProfile
from documents.models import DocumentAttachment
from .defaults import DEFAULT_TASK_TAGS, ensure_default_task_tags
from .models import Project, Tag, Task, TaskList, TaskNote
from .views import _clean_empty_list_markers, _project_detail_redirect


class ProjectTaskRedirectTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_project_detail_redirect_defaults_to_board_url(self):
        request = self.factory.post("/projects/lists/1/tasks/create/", {})

        response = _project_detail_redirect(7, request)

        self.assertEqual(response["Location"], "/projects/7/")

    def test_project_detail_redirect_preserves_master_task_list_view(self):
        request = self.factory.post(
            "/projects/tasks/1/update/",
            {"return_view": "list"},
        )

        response = _project_detail_redirect(7, request)

        self.assertEqual(response["Location"], "/projects/7/#list")


class DefaultTaskTagTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Starter Workspace")

    def test_default_task_tags_are_added_to_blank_project(self):
        project = Project.objects.create(name="Launch", business=self.business)

        ensure_default_task_tags(project)

        self.assertEqual(project.tags.count(), len(DEFAULT_TASK_TAGS))
        self.assertQuerySetEqual(
            project.tags.order_by("name").values_list("name", flat=True),
            sorted(tag["name"] for tag in DEFAULT_TASK_TAGS),
            transform=str,
        )

    def test_default_task_tags_do_not_clutter_existing_tag_sets(self):
        project = Project.objects.create(name="Custom", business=self.business)
        Tag.objects.create(project=project, name="Custom Label", color="#111111")

        ensure_default_task_tags(project)

        self.assertQuerySetEqual(
            project.tags.values_list("name", flat=True),
            ["Custom Label"],
            transform=str,
        )


class ProjectDeletePermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.business = Business.objects.create(name="Delete Test Workspace")
        self.manager = User.objects.create_user(username="manager", password="StrongPass123!")
        self.manager.profile.role = UserProfile.ROLE_MANAGER
        self.manager.profile.save()
        self.user = User.objects.create_user(username="teammate", password="StrongPass123!")
        BusinessMembership.objects.create(
            user=self.user,
            business=self.business,
            can_access_projects=True,
        )

    def test_manager_can_delete_project_board(self):
        project = Project.objects.create(name="Old Board", business=self.business)
        self.client.force_login(self.manager)

        response = self.client.post(reverse("projects:project_delete", args=[project.id]))

        self.assertRedirects(response, reverse("projects:project_list"))
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_regular_project_user_cannot_delete_project_board(self):
        project = Project.objects.create(name="Keep Board", business=self.business)
        self.client.force_login(self.user)

        response = self.client.post(reverse("projects:project_delete", args=[project.id]))

        self.assertRedirects(response, reverse("projects:project_list"))
        self.assertTrue(Project.objects.filter(id=project.id).exists())

    def test_project_delete_button_only_renders_for_managers(self):
        Project.objects.create(name="Visible Board", business=self.business)

        self.client.force_login(self.user)
        response = self.client.get(reverse("projects:project_list"))
        self.assertNotContains(response, "Delete Visible Board project board")

        self.client.force_login(self.manager)
        response = self.client.get(reverse("projects:project_list"))
        self.assertContains(response, "Delete Visible Board project board")


class TaskOverviewTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media_dir.cleanup)
        User = get_user_model()
        self.business = Business.objects.create(name="Task Overview Workspace")
        self.user = User.objects.create_user(username="task-user", password="StrongPass123!")
        BusinessMembership.objects.create(
            user=self.user,
            business=self.business,
            can_access_projects=True,
        )
        self.project = Project.objects.create(name="Alpha Project", business=self.business)
        self.task_list = TaskList.objects.create(project=self.project, name="Original List")

    def test_pending_task_overview_groups_tasks_by_project(self):
        Task.objects.create(list=self.task_list, title="Pending thing", status="TODO")
        Task.objects.create(list=self.task_list, title="Completed thing", status="DONE")
        self.client.force_login(self.user)

        response = self.client.get(reverse("projects:task_overview", args=["pending"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pending Tasks")
        self.assertContains(response, "Alpha Project")
        self.assertContains(response, "Original List")
        self.assertContains(response, "Pending thing")
        self.assertNotContains(response, "Completed thing")

    def test_completed_task_overview_has_checked_tasks_that_can_be_restored(self):
        Task.objects.create(list=self.task_list, title="Done thing", status="DONE")
        self.client.force_login(self.user)

        response = self.client.get(reverse("projects:task_overview", args=["completed"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Completed Tasks")
        self.assertContains(response, "Done thing")
        self.assertContains(response, "checked")
        self.assertContains(response, "toggleOverviewTaskStatus")

    def test_completed_task_overview_can_filter_to_original_list(self):
        other_list = TaskList.objects.create(project=self.project, name="Other List")
        Task.objects.create(list=self.task_list, title="Done in original", status="DONE")
        Task.objects.create(list=other_list, title="Done elsewhere", status="DONE")
        self.client.force_login(self.user)

        response = self.client.get(
            f"{reverse('projects:task_overview', args=['completed'])}?list={self.task_list.id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Completed Tasks: Original List")
        self.assertContains(response, "Done in original")
        self.assertNotContains(response, "Done elsewhere")

    def test_project_board_collapses_completed_tasks_into_list_link(self):
        active = Task.objects.create(list=self.task_list, title="Active task", status="TODO")
        completed = Task.objects.create(list=self.task_list, title="Finished task", status="DONE")
        self.client.force_login(self.user)

        response = self.client.get(reverse("projects:project_detail", args=[self.project.id]))

        self.assertContains(response, f'class="task-card" id="task-card-{active.id}"')
        self.assertNotContains(response, f'class="task-card" id="task-card-{completed.id}"')
        self.assertContains(response, "completed item")
        self.assertContains(
            response,
            f"{reverse('projects:task_overview', args=['completed'])}?list={self.task_list.id}",
        )

    def test_master_task_sheet_pushes_completed_tasks_to_collapsed_bottom_section(self):
        Task.objects.create(list=self.task_list, title="Active sheet task", status="TODO")
        Task.objects.create(list=self.task_list, title="Finished sheet task", status="DONE")
        self.client.force_login(self.user)

        response = self.client.get(reverse("projects:project_detail", args=[self.project.id]))
        content = response.content.decode()

        self.assertLess(content.index("Active sheet task"), content.index("data-completed-toggle-row"))
        self.assertLess(content.index("data-completed-toggle-row"), content.index("Finished sheet task"))
        self.assertContains(response, 'class="master-completed-row"')
        self.assertContains(response, "display: none; border-bottom")
        self.assertContains(response, "1</strong>")
        self.assertContains(response, "completed task</span>")

    def test_unknown_task_overview_status_returns_bad_request(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("projects:task_overview", args=["banana"]))

        self.assertEqual(response.status_code, 400)

    def test_pinned_pending_task_appears_before_unpinned_tasks(self):
        Task.objects.create(list=self.task_list, title="Normal task", status="TODO")
        pinned = Task.objects.create(list=self.task_list, title="Pinned task", status="TODO")
        pinned.is_pinned = True
        pinned.save(update_fields=["is_pinned"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("projects:task_overview", args=["pending"]))
        content = response.content.decode()

        self.assertLess(content.index("Pinned task"), content.index("Normal task"))

    def test_task_pin_endpoint_sets_pin_state(self):
        task = Task.objects.create(list=self.task_list, title="Pin me", status="TODO")
        self.client.force_login(self.user)

        response = self.client.post(reverse("projects:task_pin", args=[task.id]), {"pin": "1"})

        self.assertRedirects(response, reverse("projects:project_detail", args=[self.project.id]))
        task.refresh_from_db()
        self.assertTrue(task.is_pinned)
        self.assertIsNotNone(task.pinned_at)

    def test_task_extracts_links_from_description_and_notes(self):
        task = Task.objects.create(
            list=self.task_list,
            title="Has links",
            description="Spec: https://example.com/spec.",
        )
        TaskNote.objects.create(task=task, content="Follow up at https://example.com/note")

        self.assertEqual(
            task.extracted_links,
            ["https://example.com/spec", "https://example.com/note"],
        )
        self.assertEqual(
            [
                (link["url"], link["source_label"])
                for link in task.link_previews
            ],
            [
                ("https://example.com/spec", "Task description"),
                ("https://example.com/note", "Note 1"),
            ],
        )

    def test_project_board_renders_list_controls_and_card_previews(self):
        task = Task.objects.create(
            list=self.task_list,
            title="Preview task",
            description="Open https://example.com/task",
        )
        TaskNote.objects.create(task=task, content="First note\n- existing bullet\nhttps://example.com/note")
        TaskNote.objects.create(task=task, content="Second note")
        self.client.force_login(self.user)

        response = self.client.get(reverse("projects:project_detail", args=[self.project.id]))

        self.assertContains(response, "activateListMode('taskDesc', 'bullet')")
        self.assertContains(response, "activateListMode('editTaskDesc', 'number')")
        self.assertContains(response, "task-card-previews")
        self.assertContains(response, "Note 1")
        self.assertContains(response, "Note 2")
        self.assertContains(response, "Notes Glance")
        self.assertContains(response, "openTaskNoteFromElement")
        self.assertContains(response, "Task description Link")
        self.assertContains(response, "Note 1 Link")
        self.assertContains(response, "task-link-page-preview")
        self.assertContains(response, '<iframe src="https://example.com/note"', html=False)
        self.assertContains(response, "https://example.com/task")

    def test_follow_up_notes_are_ordered_oldest_to_newest(self):
        task = Task.objects.create(list=self.task_list, title="Ordered notes")
        old_note = TaskNote.objects.create(task=task, content="Old note")
        new_note = TaskNote.objects.create(task=task, content="New note")
        TaskNote.objects.filter(id=old_note.id).update(created_at=timezone.now() - timezone.timedelta(days=1))
        TaskNote.objects.filter(id=new_note.id).update(created_at=timezone.now())

        self.assertEqual(list(task.notes.values_list("content", flat=True)), ["Old note", "New note"])
        self.assertEqual(task.latest_note.content, "New note")

    def test_project_board_does_not_render_extra_save_changes_note_field(self):
        Task.objects.create(list=self.task_list, title="Clean modal")
        self.client.force_login(self.user)

        response = self.client.get(reverse("projects:project_detail", args=[self.project.id]))

        self.assertNotContains(response, "Add Follow-up Note with Save")

    def test_save_changes_updates_existing_notes_and_bottom_new_note(self):
        task = Task.objects.create(list=self.task_list, title="Update with notes", description="Before")
        note = TaskNote.objects.create(task=task, content="Original note")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("projects:task_update", args=[task.id]),
            {
                "title": "Update with notes",
                "description": "After",
                "priority": "MEDIUM",
                "status": "TODO",
                "list": self.task_list.id,
                f"note_content_{note.id}": "Edited from Save Changes",
                "new_note_content": "Added from bottom composer",
            },
        )

        self.assertRedirects(response, reverse("projects:project_detail", args=[self.project.id]))
        note.refresh_from_db()
        self.assertEqual(note.content, "Edited from Save Changes")
        self.assertTrue(task.notes.filter(content="Added from bottom composer").exists())

    def test_follow_up_note_can_be_edited(self):
        task = Task.objects.create(list=self.task_list, title="Editable note")
        note = TaskNote.objects.create(task=task, content="Original note")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("projects:task_note_update", args=[note.id]),
            {"content": "Updated note"},
        )

        self.assertRedirects(response, reverse("projects:project_detail", args=[self.project.id]))
        note.refresh_from_db()
        self.assertEqual(note.content, "Updated note")

    def test_follow_up_note_ajax_update_stays_in_modal(self):
        task = Task.objects.create(list=self.task_list, title="Ajax note")
        note = TaskNote.objects.create(task=task, content="Original note")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("projects:task_note_update", args=[note.id]),
            {"content": "Updated inline"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            "success": True,
            "note": {
                "id": note.id,
                "content": "Updated inline",
                "date": note.created_at.strftime("%b %d, %Y, %I:%M %p"),
                "attachments": [],
            },
        })

    def test_project_board_renders_note_attachments_for_card_preview_and_modal_cache(self):
        task = Task.objects.create(list=self.task_list, title="Attachment preview")
        note = TaskNote.objects.create(task=task, content="Review attached brief")
        DocumentAttachment.objects.create(
            business=self.business,
            task_note=note,
            uploaded_by=self.user,
            original_filename="brief.pdf",
            file=SimpleUploadedFile("brief.pdf", b"pdf data", content_type="application/pdf"),
            content_type="application/pdf",
            size=8,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("projects:project_detail", args=[self.project.id]))

        self.assertContains(response, "brief.pdf")
        self.assertContains(response, "note-attachment-list")
        self.assertContains(response, "cache-attachment")

    def test_save_changes_attaches_file_to_existing_follow_up_note(self):
        task = Task.objects.create(list=self.task_list, title="Update with file", description="Before")
        note = TaskNote.objects.create(task=task, content="Original note")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("projects:task_update", args=[task.id]),
            {
                "title": "Update with file",
                "description": "After",
                "priority": "MEDIUM",
                "status": "TODO",
                "list": self.task_list.id,
                f"note_content_{note.id}": "Edited and attached",
                f"note_attachments_{note.id}": SimpleUploadedFile("scope.txt", b"scope", content_type="text/plain"),
            },
        )

        self.assertRedirects(response, reverse("projects:project_detail", args=[self.project.id]))
        note.refresh_from_db()
        self.assertEqual(note.content, "Edited and attached")
        attachment = note.attachments.get()
        self.assertEqual(attachment.original_filename, "scope.txt")
        self.assertEqual(attachment.business, self.business)

    def test_save_changes_attaches_file_to_bottom_new_follow_up_note(self):
        task = Task.objects.create(list=self.task_list, title="New note with file", description="Before")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("projects:task_update", args=[task.id]),
            {
                "title": "New note with file",
                "description": "After",
                "priority": "MEDIUM",
                "status": "TODO",
                "list": self.task_list.id,
                "new_note_content": "Added with attachment",
                "new_note_attachments": SimpleUploadedFile("receipt.jpg", b"image", content_type="image/jpeg"),
            },
        )

        self.assertRedirects(response, reverse("projects:project_detail", args=[self.project.id]))
        note = task.notes.get(content="Added with attachment")
        self.assertEqual(note.attachments.get().original_filename, "receipt.jpg")

    def test_follow_up_note_ajax_update_can_attach_file(self):
        task = Task.objects.create(list=self.task_list, title="Ajax file")
        note = TaskNote.objects.create(task=task, content="Original note")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("projects:task_note_update", args=[note.id]),
            {
                "content": "Updated inline",
                "attachments": SimpleUploadedFile("inline.txt", b"inline", content_type="text/plain"),
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        attachment = note.attachments.get()
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["note"]["attachments"][0]["name"], "inline.txt")
        self.assertEqual(attachment.original_filename, "inline.txt")

    def test_follow_up_note_can_be_deleted(self):
        task = Task.objects.create(list=self.task_list, title="Delete note")
        note = TaskNote.objects.create(task=task, content="Remove me")
        self.client.force_login(self.user)

        response = self.client.post(reverse("projects:task_note_delete", args=[note.id]))

        self.assertRedirects(response, reverse("projects:project_detail", args=[self.project.id]))
        self.assertFalse(TaskNote.objects.filter(id=note.id).exists())

    def test_follow_up_note_ajax_delete_stays_in_modal(self):
        task = Task.objects.create(list=self.task_list, title="Ajax delete note")
        note = TaskNote.objects.create(task=task, content="Remove inline")
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("projects:task_note_delete", args=[note.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True, "note_id": note.id})
        self.assertFalse(TaskNote.objects.filter(id=note.id).exists())

    def test_quick_add_creates_tasks_from_bulleted_or_numbered_lines(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("projects:task_quick_add", args=[self.project.id]),
            {"title": "- First item\n- Nested idea\n1. Numbered item"},
        )

        self.assertRedirects(response, f"{reverse('projects:project_detail', args=[self.project.id])}")
        self.assertQuerySetEqual(
            Task.objects.filter(list=self.task_list).order_by("created_at").values_list("title", flat=True),
            ["First item", "Nested idea", "Numbered item"],
            transform=str,
        )

    def test_empty_list_markers_are_removed_before_save(self):
        self.assertEqual(
            _clean_empty_list_markers("- First\n-\n1.\n2. Second\n*"),
            "- First\n2. Second",
        )
