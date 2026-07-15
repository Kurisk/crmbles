from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Business, BusinessMembership


class DashboardMetricLinkTests(TestCase):
    def test_task_and_document_metrics_link_to_filtered_pages(self):
        User = get_user_model()
        business = Business.objects.create(name="Dashboard Workspace")
        user = User.objects.create_user(username="dashboard-user", password="StrongPass123!")
        BusinessMembership.objects.create(
            user=user,
            business=business,
            can_access_projects=True,
            can_access_documents=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))

        self.assertContains(response, reverse("projects:task_overview", args=["pending"]))
        self.assertContains(response, reverse("projects:task_overview", args=["completed"]))
        self.assertContains(response, reverse("documents:document_list"))
        self.assertNotContains(response, 'href="#urgent-tasks"')
        self.assertNotContains(response, 'href="#task-progress"')
        self.assertNotContains(response, 'href="#recent-notes"')

    def test_dashboard_hides_sections_without_business_access(self):
        User = get_user_model()
        business = Business.objects.create(name="Documents Workspace")
        user = User.objects.create_user(username="docs-only-user", password="StrongPass123!")
        BusinessMembership.objects.create(
            user=user,
            business=business,
            can_access_documents=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))

        self.assertContains(response, reverse("documents:document_list"))
        self.assertContains(response, "Saved Documents")
        self.assertContains(response, "Recent Ideas")
        self.assertNotContains(response, reverse("projects:project_list"))
        self.assertNotContains(response, "Active Projects")
        self.assertNotContains(response, "Pending Tasks")
        self.assertNotContains(response, reverse("finance:dashboard"))
        self.assertNotContains(response, "Pending Invoices")
        self.assertNotContains(response, "Pending Expenses")

    def test_sidebar_uses_clients_access_separately_from_vendors(self):
        User = get_user_model()
        business = Business.objects.create(name="Client Sidebar Workspace")
        user = User.objects.create_user(username="client-sidebar-user", password="StrongPass123!")
        BusinessMembership.objects.create(
            user=user,
            business=business,
            can_access_clients=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))

        self.assertContains(response, reverse("clients:client_list"))
        self.assertNotContains(response, reverse("vendors:vendor_list"))


class PublicProductInfoTests(TestCase):
    def test_faq_page_has_search_contact_and_footer_links(self):
        response = self.client.get(reverse("core:faq"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Search FAQ")
        self.assertContains(response, "dowitzgame@gmail.com")
        self.assertContains(response, "CRMbles v0.2.0")
        self.assertContains(response, reverse("core:latest_update"))
        self.assertContains(response, "Vendors, Clients, And Finance")

    def test_latest_update_page_lists_current_release_items(self):
        response = self.client.get(reverse("core:latest_update"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Version 0.2.0")
        self.assertContains(response, "Public Access Prep")
        self.assertContains(response, "Added a searchable FAQ page")

    def test_public_welcome_includes_faq_and_support_footer(self):
        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="welcome-page"')
        self.assertContains(response, 'class="welcome-shell"')
        self.assertContains(response, 'welcome-card')
        self.assertContains(response, reverse("core:faq"))
        self.assertContains(response, "dowitzgame@gmail.com")
        self.assertContains(response, "Latest Update")
