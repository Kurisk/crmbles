from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.pinning import apply_pin_state, safe_redirect_target
from .models import Client, ClientOpportunity, ClientTag


def client_list(request):
    clients = Client.objects.filter(business=request.business).prefetch_related('tags', 'opportunities')
    all_tags = ClientTag.objects.filter(business=request.business)
    active_tags = all_tags.filter(clients__isnull=False).distinct()

    q = request.GET.get('q', '').strip()
    if q:
        clients = clients.filter(
            Q(name__icontains=q) |
            Q(company__icontains=q) |
            Q(contact_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q) |
            Q(website__icontains=q) |
            Q(notes__icontains=q)
        )

    context = {
        'clients': clients,
        'all_tags': all_tags,
        'active_tags': active_tags,
        'q': q,
        'total_clients': clients.count(),
        'lead_clients': clients.filter(status=Client.STATUS_LEAD).count(),
        'active_clients': clients.filter(status=Client.STATUS_ACTIVE).count(),
        'past_clients': clients.filter(status=Client.STATUS_PAST).count(),
        'client_statuses': Client.STATUS_CHOICES,
        'opportunity_statuses': ClientOpportunity.STATUS_CHOICES,
    }
    return render(request, 'clients/client_list.html', context)


def _opportunities_from_post(request):
    opportunities = []
    names = request.POST.getlist('opportunity_name[]')
    descriptions = request.POST.getlist('opportunity_desc[]')
    estimates = request.POST.getlist('opportunity_estimate[]')
    statuses = request.POST.getlist('opportunity_status[]')
    notes = request.POST.getlist('opportunity_notes[]')
    valid_statuses = {status for status, _label in ClientOpportunity.STATUS_CHOICES}

    for index, raw_name in enumerate(names):
        name = raw_name.strip()
        if not name:
            continue
        estimate_value = estimates[index].strip() if index < len(estimates) else ''
        estimate = None
        if estimate_value:
            try:
                estimate = Decimal(estimate_value)
            except (InvalidOperation, TypeError):
                estimate = None
        status = statuses[index] if index < len(statuses) and statuses[index] in valid_statuses else ClientOpportunity.STATUS_OPEN
        opportunities.append({
            'name': name,
            'description': descriptions[index].strip() if index < len(descriptions) else '',
            'estimate': estimate,
            'status': status,
            'notes': notes[index].strip() if index < len(notes) else '',
        })
    return opportunities


def _sync_opportunities(client, opportunities):
    client.opportunities.all().delete()
    ClientOpportunity.objects.bulk_create([
        ClientOpportunity(client=client, **opportunity)
        for opportunity in opportunities
    ])


def _save_client_from_post(request, client=None):
    name = request.POST.get('name', '').strip()
    if not name:
        return None, 'Client name is required.'

    status = request.POST.get('status', Client.STATUS_LEAD)
    valid_statuses = {choice for choice, _label in Client.STATUS_CHOICES}
    if status not in valid_statuses:
        status = Client.STATUS_LEAD

    if client is None:
        client = Client(business=request.business)

    client.name = name
    client.company = request.POST.get('company', '').strip()
    client.contact_name = request.POST.get('contact_name', '').strip()
    client.website = request.POST.get('website', '').strip()
    client.email = request.POST.get('email', '').strip()
    client.phone = request.POST.get('phone', '').strip()
    client.status = status
    client.source = request.POST.get('source', '').strip()
    client.notes = request.POST.get('notes', '')
    client.save()
    client.tags.set(request.POST.getlist('tags'))
    _sync_opportunities(client, _opportunities_from_post(request))
    return client, None


@require_POST
def client_create(request):
    client, error = _save_client_from_post(request)
    if error:
        messages.error(request, f'Failed to create client: {error}')
    else:
        messages.success(request, f"Client '{client.name}' added successfully.")
    return redirect('clients:client_list')


@require_POST
def client_update(request, client_id):
    client = get_object_or_404(Client, pk=client_id, business=request.business)
    client, error = _save_client_from_post(request, client)
    if error:
        messages.error(request, f'Failed to update client: {error}')
    else:
        messages.success(request, f"Client '{client.name}' updated successfully.")
    return redirect('clients:client_list')


@require_POST
def client_delete(request, client_id):
    client = get_object_or_404(Client, pk=client_id, business=request.business)
    name = client.name
    client.delete()
    messages.success(request, f"Client '{name}' deleted successfully.")
    return redirect('clients:client_list')


@require_POST
def client_pin(request, client_id):
    client = get_object_or_404(Client, pk=client_id, business=request.business)
    apply_pin_state(client, request.POST.get('pin') == '1')
    return redirect(safe_redirect_target(request, reverse('clients:client_list')))


@require_POST
def client_tag_create(request):
    name = request.POST.get('name', '').strip()
    color = request.POST.get('color', '#0ea5e9').strip() or '#0ea5e9'
    if color and not color.startswith('#'):
        color = f'#{color}'

    if name:
        tag, created = ClientTag.objects.get_or_create(
            business=request.business,
            name=name,
            defaults={'color': color},
        )
        if created:
            messages.success(request, f"Tag '{name}' created successfully.")
        else:
            messages.info(request, f"Tag '{name}' already exists.")
    else:
        messages.error(request, 'Tag name is required.')
    return redirect('clients:client_list')
