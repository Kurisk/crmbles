from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Business, BusinessMembership
from .models import Vendor


class VendorPinTests(TestCase):
    def test_vendor_pin_endpoint_moves_vendor_to_front(self):
        User = get_user_model()
        business = Business.objects.create(name="Vendor Workspace")
        user = User.objects.create_user(username="vendor-user", password="StrongPass123!")
        BusinessMembership.objects.create(
            user=user,
            business=business,
            can_access_vendors=True,
        )
        Vendor.objects.create(business=business, name="Normal Vendor")
        pinned = Vendor.objects.create(business=business, name="Pinned Vendor")
        self.client.force_login(user)

        response = self.client.post(reverse("vendors:vendor_pin", args=[pinned.id]), {"pin": "1"})

        self.assertRedirects(response, reverse("vendors:vendor_list"))
        pinned.refresh_from_db()
        self.assertTrue(pinned.is_pinned)
        list_response = self.client.get(reverse("vendors:vendor_list"))
        content = list_response.content.decode()
        self.assertLess(content.index("Pinned Vendor"), content.index("Normal Vendor"))
