from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import Business, BusinessMembership, UserProfile
from .defaults import DEFAULT_TASK_TAGS, ensure_default_task_tags
from .models import Project, Tag, Task, TaskList
from .views import _project_detail_redirect


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
