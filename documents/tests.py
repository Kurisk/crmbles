from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
import tempfile

from accounts.models import Business, BusinessMembership
from projects.models import Project
from .models import Document, DocumentAttachment


class DocumentListSearchTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media_dir.cleanup)
        User = get_user_model()
        self.business = Business.objects.create(name="Docs Workspace")
        self.user = User.objects.create_user(username="docs-user", password="StrongPass123!")
        BusinessMembership.objects.create(
            user=self.user,
            business=self.business,
            can_access_documents=True,
        )
        self.project = Project.objects.create(name="Launch Plan", business=self.business)

    def test_document_list_renders_working_search_controls(self):
        Document.objects.create(
            business=self.business,
            project=self.project,
            title="General Ideas",
            content="Vendor research and launch notes.",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("documents:document_list"))

        self.assertContains(response, 'id="documentSearch"')
        self.assertContains(response, 'data-document-search="General Ideas Launch Plan')
        self.assertContains(response, 'id="documentSearchEmpty"')
        self.assertContains(response, "filterDocuments")

    def test_document_pin_endpoint_moves_document_to_front(self):
        Document.objects.create(
            business=self.business,
            title="Normal Doc",
            content="Standard reference.",
        )
        pinned = Document.objects.create(
            business=self.business,
            title="Pinned Doc",
            content="Important reference.",
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("documents:document_pin", args=[pinned.id]), {"pin": "1"})

        self.assertRedirects(response, reverse("documents:document_list"))
        pinned.refresh_from_db()
        self.assertTrue(pinned.is_pinned)
        list_response = self.client.get(reverse("documents:document_list"))
        content = list_response.content.decode()
        self.assertLess(content.index("Pinned Doc"), content.index("Normal Doc"))

    def test_file_library_uploads_standalone_attachments(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile("reference.txt", b"hello file", content_type="text/plain")

        response = self.client.post(
            reverse("documents:attachment_upload"),
            {"title": "Reference File", "files": upload},
        )

        self.assertRedirects(response, reverse("documents:document_list"))
        attachment = DocumentAttachment.objects.get()
        self.assertEqual(attachment.business, self.business)
        self.assertEqual(attachment.title, "Reference File")
        self.assertEqual(attachment.original_filename, "reference.txt")
        self.assertEqual(attachment.content_type, "text/plain")
        self.assertIsNone(attachment.document)
        self.assertIsNone(attachment.task_note)

        list_response = self.client.get(reverse("documents:document_list"))
        self.assertContains(list_response, "File Library")
        self.assertContains(list_response, "Reference File")

    def test_file_library_deletes_attachment_record(self):
        attachment = DocumentAttachment.objects.create(
            business=self.business,
            uploaded_by=self.user,
            original_filename="old.txt",
            file=SimpleUploadedFile("old.txt", b"delete me", content_type="text/plain"),
            content_type="text/plain",
            size=9,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("documents:attachment_delete", args=[attachment.id]))

        self.assertRedirects(response, reverse("documents:document_list"))
        self.assertFalse(DocumentAttachment.objects.filter(id=attachment.id).exists())
