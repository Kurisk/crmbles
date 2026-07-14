from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Business, BusinessMembership, UserProfile


class SignupFlowTests(TestCase):
    def test_root_shows_public_welcome_for_logged_out_visitors(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CRMbles")
        self.assertContains(response, "Sign In")
        self.assertContains(response, "Sign Up")

    def test_signup_creates_workspace_owner_membership(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "business_name": "Acme Desk",
                "username": "owner",
                "email": "owner@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("core:dashboard"))
        user = get_user_model().objects.get(username="owner")
        business = Business.objects.get(name="Acme Desk")
        membership = BusinessMembership.objects.get(user=user, business=business)
        self.assertEqual(user.profile.role, UserProfile.ROLE_USER)
        self.assertFalse(user.profile.is_manager)
        self.assertTrue(membership.can_access_projects)
        self.assertTrue(membership.can_access_documents)
        self.assertTrue(membership.can_access_vendors)
        self.assertTrue(membership.can_access_finance)
        self.assertTrue(membership.can_manage_accounts)
