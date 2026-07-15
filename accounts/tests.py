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
        self.assertTrue(membership.can_access_clients)
        self.assertTrue(membership.can_access_finance)
        self.assertTrue(membership.can_manage_accounts)


class ProfileFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="teammate", password="StrongPass123!", email="old@example.com")
        self.supervisor = User.objects.create_user(username="boss", password="StrongPass123!")
        self.user.profile.team = "Operations"
        self.user.profile.supervisor = self.supervisor
        self.user.profile.save()

    def test_user_can_update_personal_profile_details(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "first_name": "Taylor",
                "last_name": "Reed",
                "email": "taylor@example.com",
                "job_title": "Coordinator",
                "office": "Suite 12",
                "phone_number": "555-0100",
                "mobile_number": "555-0199",
                "address_line1": "123 Main St",
                "address_line2": "Apt 4",
                "city": "Boston",
                "state": "MA",
                "postal_code": "02110",
                "country": "United States",
                "emergency_contact_name": "Casey",
                "emergency_contact_phone": "555-0111",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, "Taylor")
        self.assertEqual(self.user.email, "taylor@example.com")
        self.assertEqual(self.user.profile.office, "Suite 12")
        self.assertEqual(self.user.profile.phone_number, "555-0100")

    def test_user_cannot_update_manager_owned_fields_from_profile(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile"),
            {
                "email": "teammate@example.com",
                "team": "Executive",
                "supervisor": "",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.team, "Operations")
        self.assertEqual(self.user.profile.supervisor, self.supervisor)

    def test_profile_page_handles_missing_supervisor(self):
        self.user.profile.supervisor = None
        self.user.profile.save()
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "None")
        self.assertContains(response, reverse("accounts:password_change"))

    def test_authenticated_user_can_change_password_from_profile_flow(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "StrongPass123!",
                "new_password1": "NewStrongPass123!",
                "new_password2": "NewStrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("accounts:password_change_done"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass123!"))


class BusinessPinTests(TestCase):
    def test_manager_can_pin_business_to_front(self):
        User = get_user_model()
        manager = User.objects.create_user(username="manager", password="StrongPass123!")
        manager.profile.grant_manager_access()
        manager.profile.save()
        Business.objects.create(name="Normal Business")
        pinned = Business.objects.create(name="Pinned Business")
        self.client.force_login(manager)

        response = self.client.post(reverse("accounts:business_pin", args=[pinned.id]), {"pin": "1"})

        self.assertRedirects(response, reverse("accounts:business_list"))
        pinned.refresh_from_db()
        self.assertTrue(pinned.is_pinned)
        list_response = self.client.get(reverse("accounts:business_list"))
        business_names = [business.name for business in list_response.context["businesses"]]
        self.assertEqual(business_names[0], "Pinned Business")
        self.assertIn("Normal Business", business_names)


class AccountManagerAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.manager = User.objects.create_user(username="account-manager", password="StrongPass123!")
        self.manager.profile.grant_manager_access()
        self.manager.profile.save()
        self.user = User.objects.create_user(username="managed-user", password="StrongPass123!")
        self.client.force_login(self.manager)

    def test_regular_user_cannot_manage_accounts_even_with_legacy_permission_flag(self):
        User = get_user_model()
        business = Business.objects.create(name="Account Workspace")
        user = User.objects.create_user(username="regular-manager-flag", password="StrongPass123!")
        user.profile.can_manage_accounts = True
        user.profile.save()
        BusinessMembership.objects.create(
            user=user,
            business=business,
            can_manage_accounts=True,
        )
        self.client.force_login(user)
        session = self.client.session
        session["active_business_id"] = business.pk
        session.save()

        response = self.client.get(reverse("accounts:user_list"))

        self.assertRedirects(response, reverse("core:dashboard"))

    def test_account_list_shows_deactivate_and_delete_warning(self):
        response = self.client.get(reverse("accounts:user_list"))

        self.assertContains(response, reverse("accounts:user_deactivate", args=[self.user.id]))
        self.assertContains(response, reverse("accounts:user_delete", args=[self.user.id]))
        self.assertContains(
            response,
            "Anything created on the system by this user will be deleted with the user and may be available with a backup upon request, but not guaranteed.",
        )

    def test_manager_can_deactivate_and_reactivate_user(self):
        response = self.client.post(reverse("accounts:user_deactivate", args=[self.user.id]))
        self.assertRedirects(response, reverse("accounts:user_list"))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        response = self.client.post(reverse("accounts:user_activate", args=[self.user.id]))
        self.assertRedirects(response, reverse("accounts:user_list"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_manager_can_delete_user(self):
        response = self.client.post(reverse("accounts:user_delete", args=[self.user.id]))

        self.assertRedirects(response, reverse("accounts:user_list"))
        self.assertFalse(get_user_model().objects.filter(pk=self.user.pk).exists())

    def test_manager_cannot_deactivate_or_delete_self(self):
        response = self.client.post(reverse("accounts:user_deactivate", args=[self.manager.id]))
        self.assertRedirects(response, reverse("accounts:user_list"))
        self.manager.refresh_from_db()
        self.assertTrue(self.manager.is_active)

        response = self.client.post(reverse("accounts:user_delete", args=[self.manager.id]))
        self.assertRedirects(response, reverse("accounts:user_list"))
        self.assertTrue(get_user_model().objects.filter(pk=self.manager.pk).exists())

    def test_cannot_remove_last_active_manager(self):
        self.manager.delete()
        User = get_user_model()
        superuser = User.objects.create_superuser(username="superuser", password="StrongPass123!")
        target_manager = User.objects.create_user(username="last-manager", password="StrongPass123!")
        target_manager.profile.grant_manager_access()
        target_manager.profile.save()
        self.client.force_login(superuser)

        response = self.client.post(reverse("accounts:user_deactivate", args=[target_manager.id]))
        self.assertRedirects(response, reverse("accounts:user_list"))
        target_manager.refresh_from_db()
        self.assertTrue(target_manager.is_active)
