from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Business, BusinessMembership
from .models import Client, ClientOpportunity, ClientTag


class ClientDirectoryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.business = Business.objects.create(name='Client Workspace')
        self.user = User.objects.create_user(username='client-user', password='StrongPass123!')
        BusinessMembership.objects.create(
            user=self.user,
            business=self.business,
            can_access_clients=True,
            can_access_finance=True,
        )
        self.client.force_login(self.user)
        session = self.client.session
        session['active_business_id'] = self.business.pk
        session.save()

    def test_client_create_saves_tags_and_opportunities(self):
        tag = ClientTag.objects.create(business=self.business, name='Referral', color='#0ea5e9')

        response = self.client.post(
            reverse('clients:client_create'),
            {
                'name': 'Acme Corp',
                'company': 'Acme Holdings',
                'contact_name': 'Avery Adams',
                'email': 'avery@example.com',
                'status': 'ACTIVE',
                'tags': [str(tag.pk)],
                'opportunity_name[]': ['Website refresh'],
                'opportunity_desc[]': ['Design and build'],
                'opportunity_estimate[]': ['2500.00'],
                'opportunity_status[]': ['OPEN'],
                'opportunity_notes[]': ['Discovery complete'],
            },
        )

        self.assertRedirects(response, reverse('clients:client_list'))
        saved_client = Client.objects.get(name='Acme Corp')
        self.assertEqual(saved_client.business, self.business)
        self.assertEqual(saved_client.tags.get(), tag)
        opportunity = saved_client.opportunities.get()
        self.assertEqual(opportunity.name, 'Website refresh')
        self.assertEqual(opportunity.estimate, 2500)

    def test_client_pin_endpoint_moves_client_to_front(self):
        Client.objects.create(business=self.business, name='Normal Client')
        pinned = Client.objects.create(business=self.business, name='Pinned Client')

        response = self.client.post(reverse('clients:client_pin', args=[pinned.id]), {'pin': '1'})

        self.assertRedirects(response, reverse('clients:client_list'))
        pinned.refresh_from_db()
        self.assertTrue(pinned.is_pinned)
        list_response = self.client.get(reverse('clients:client_list'))
        content = list_response.content.decode()
        self.assertLess(content.index('Pinned Client'), content.index('Normal Client'))


class ClientAccessTests(TestCase):
    def test_vendor_access_does_not_grant_client_access(self):
        User = get_user_model()
        business = Business.objects.create(name='Vendor Only Workspace')
        user = User.objects.create_user(username='vendor-only-user', password='StrongPass123!')
        BusinessMembership.objects.create(
            user=user,
            business=business,
            can_access_vendors=True,
        )
        self.client.force_login(user)
        session = self.client.session
        session['active_business_id'] = business.pk
        session.save()

        response = self.client.get(reverse('clients:client_list'))

        self.assertRedirects(response, reverse('core:dashboard'))
