from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Business, BusinessMembership
from projects.models import Project
from .models import Document


class DocumentListSearchTests(TestCase):
    def setUp(self):
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
