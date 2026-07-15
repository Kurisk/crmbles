from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Business
from clients.models import Client
from vendors.models import Vendor
from .models import Expense, ExpenseCategory, IndustryExpenseItem, Invoice


class ExpenseVendorDefaultTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="manager",
            password="pass12345",
        )
        self.profile = self.user.profile
        self.profile.grant_manager_access()
        self.profile.save()
        self.business = Business.objects.create(name="Test Business")
        self.client.force_login(self.user)
        session = self.client.session
        session["active_business_id"] = self.business.pk
        session.save()

    def test_expense_uses_vendor_default_category(self):
        category = ExpenseCategory.objects.create(
            business=self.business,
            name="Inventory",
            color="#10b981",
        )
        vendor = Vendor.objects.create(
            business=self.business,
            name="Local Supplier",
            default_expense_category=category,
        )

        response = self.client.post(
            reverse("finance:expense_create"),
            {
                "title": "Weekly purchase",
                "amount": "120.00",
                "expense_date": "2026-07-08",
                "vendor": str(vendor.pk),
                "status": "PAID",
            },
        )

        self.assertRedirects(response, reverse("finance:dashboard"))
        expense = Expense.objects.get(title="Weekly purchase")
        self.assertEqual(expense.business, self.business)
        self.assertEqual(expense.vendor, vendor)
        self.assertIsNone(expense.industry_item)
        self.assertEqual(expense.category, category)

    def test_legacy_selected_industry_item_sets_category(self):
        selected_category = ExpenseCategory.objects.create(
            business=self.business,
            name="Selected default",
            color="#ef4444",
        )
        selected_item = IndustryExpenseItem.objects.create(
            business=self.business,
            industry="Retail",
            name="Trade show booth",
            category=selected_category,
        )
        vendor = Vendor.objects.create(
            business=self.business,
            name="Event Supplier",
        )

        response = self.client.post(
            reverse("finance:expense_create"),
            {
                "title": "Expo materials",
                "amount": "300.00",
                "expense_date": "2026-07-08",
                "vendor": str(vendor.pk),
                "industry_item": str(selected_item.pk),
                "status": "PAID",
            },
        )

        self.assertRedirects(response, reverse("finance:dashboard"))
        expense = Expense.objects.get(title="Expo materials")
        self.assertEqual(expense.industry_item, selected_item)
        self.assertEqual(expense.category, selected_category)

    def test_expense_line_items_roll_up_to_total(self):
        vendor = Vendor.objects.create(
            business=self.business,
            name="Travel Supplier",
        )

        response = self.client.post(
            reverse("finance:expense_create"),
            {
                "title": "Client trip",
                "amount": "0.00",
                "expense_date": "2026-07-08",
                "vendor": str(vendor.pk),
                "status": "PAID",
                "line_item_name[]": [
                    "Ticket 1",
                    "Ticket 2",
                    "Insurance policy 1",
                    "Insurance policy 2",
                ],
                "line_item_amount[]": ["150.00", "150.00", "20.00", "20.00"],
            },
        )

        self.assertRedirects(response, reverse("finance:dashboard"))
        expense = Expense.objects.get(title="Client trip")
        self.assertEqual(expense.amount, 340)
        self.assertEqual(expense.line_items.count(), 4)

    def test_invoice_line_items_roll_up_to_total(self):
        response = self.client.post(
            reverse("finance:invoice_create"),
            {
                "client_name": "Acme Corp",
                "title": "Travel reimbursement",
                "amount": "0.00",
                "invoice_date": "2026-07-08",
                "status": "SENT",
                "line_item_name[]": [
                    "Ticket 1",
                    "Ticket 2",
                    "Insurance policy 1",
                    "Insurance policy 2",
                ],
                "line_item_amount[]": ["150.00", "150.00", "20.00", "20.00"],
            },
        )

        self.assertRedirects(response, reverse("finance:dashboard"))
        invoice = Invoice.objects.get(title="Travel reimbursement")
        self.assertEqual(invoice.amount, 340)
        self.assertEqual(invoice.line_items.count(), 4)

    def test_invoice_can_link_to_client_record(self):
        client = Client.objects.create(
            business=self.business,
            name="Acme Corp",
            company="Acme Holdings",
        )

        response = self.client.post(
            reverse("finance:invoice_create"),
            {
                "client": str(client.pk),
                "client_name": "Old typed name",
                "title": "Monthly retainer",
                "amount": "500.00",
                "invoice_date": "2026-07-08",
                "status": "SENT",
            },
        )

        self.assertRedirects(response, reverse("finance:dashboard"))
        invoice = Invoice.objects.get(title="Monthly retainer")
        self.assertEqual(invoice.client, client)
        self.assertEqual(invoice.client_name, client.name)
