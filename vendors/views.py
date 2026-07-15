from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from core.pinning import apply_pin_state, safe_redirect_target
from finance.models import ExpenseCategory, IndustryExpenseItem
from .models import Vendor, VendorTag, VendorService

def vendor_list(request):
    """
    Renders the central Vendor Directory. Supporting prefetch caching,
    search parameters, and workspace-level stats metrics.
    """
    vendors = Vendor.objects.filter(business=request.business).prefetch_related('tags', 'services').order_by('-is_pinned', '-pinned_at', 'name')
    all_tags = VendorTag.objects.filter(business=request.business)
    all_categories = ExpenseCategory.objects.filter(business=request.business)
    industry_items = IndustryExpenseItem.objects.filter(business=request.business, is_active=True).select_related('category')
    active_tags = all_tags.filter(vendors__isnull=False).distinct()
    
    # Handle Search Queries
    q = request.GET.get('q', '')
    if q:
        vendors = vendors.filter(
            Q(name__icontains=q) | 
            Q(notes__icontains=q) | 
            Q(website__icontains=q)
        )
        
    # Calculate Workspace Metrics
    total_vendors = vendors.count()
    purchased_vendors = vendors.filter(has_purchased=True).count()
    researched_vendors = total_vendors - purchased_vendors
    
    context = {
        'vendors': vendors,
        'all_tags': all_tags,
        'all_categories': all_categories,
        'industry_items': industry_items,
        'active_tags': active_tags,
        'q': q,
        'total_vendors': total_vendors,
        'purchased_vendors': purchased_vendors,
        'researched_vendors': researched_vendors
    }
    return render(request, 'vendors/vendor_list.html', context)


@require_POST
def vendor_create(request):
    """
    Saves a new researched Vendor / Supplier to the database.
    """
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    website = request.POST.get('website', '')
    email = request.POST.get('email', '')
    phone = request.POST.get('phone', '')
    default_category_id = request.POST.get('default_expense_category')
    default_industry_item_id = request.POST.get('default_industry_item')
    notes = request.POST.get('notes', '')
    has_purchased = 'has_purchased' in request.POST
    tag_ids = request.POST.getlist('tags')
    
    if name:
        default_category = get_object_or_404(ExpenseCategory, pk=default_category_id, business=request.business) if default_category_id else None
        default_industry_item = get_object_or_404(IndustryExpenseItem, pk=default_industry_item_id, business=request.business) if default_industry_item_id else None
        vendor = Vendor.objects.create(
            business=request.business,
            name=name,
            description=description,
            website=website,
            email=email,
            phone=phone,
            default_expense_category=default_category,
            default_industry_item=default_industry_item,
            notes=notes,
            has_purchased=has_purchased
        )
        if tag_ids:
            vendor.tags.set(tag_ids)
            
        # Parse and sync services array
        service_names = request.POST.getlist('service_name[]')
        service_descs = request.POST.getlist('service_desc[]')
        service_prices = request.POST.getlist('service_price[]')
        service_notes = request.POST.getlist('service_notes[]')
        
        for i in range(len(service_names)):
            s_name = service_names[i].strip()
            if s_name:
                s_desc = service_descs[i].strip() if i < len(service_descs) else ''
                s_price = service_prices[i].strip() if i < len(service_prices) else ''
                s_note = service_notes[i].strip() if i < len(service_notes) else ''
                VendorService.objects.create(
                    vendor=vendor,
                    name=s_name,
                    description=s_desc,
                    price=s_price,
                    notes=s_note
                )
                
        messages.success(request, f"Vendor '{name}' added successfully.")
    else:
        messages.error(request, "Failed to create vendor: Name is required.")
        
    return redirect('vendors:vendor_list')


@require_POST
def vendor_update(request, vendor_id):
    """
    Updates details, contact info, notes, and purchases status for an existing vendor.
    """
    vendor = get_object_or_404(Vendor, pk=vendor_id, business=request.business)
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    website = request.POST.get('website', '')
    email = request.POST.get('email', '')
    phone = request.POST.get('phone', '')
    default_category_id = request.POST.get('default_expense_category')
    default_industry_item_id = request.POST.get('default_industry_item')
    notes = request.POST.get('notes', '')
    has_purchased = 'has_purchased' in request.POST
    tag_ids = request.POST.getlist('tags')
    
    if name:
        vendor.name = name
        vendor.description = description
        vendor.website = website
        vendor.email = email
        vendor.phone = phone
        vendor.default_expense_category = get_object_or_404(ExpenseCategory, pk=default_category_id, business=request.business) if default_category_id else None
        vendor.default_industry_item = get_object_or_404(IndustryExpenseItem, pk=default_industry_item_id, business=request.business) if default_industry_item_id else None
        vendor.notes = notes
        vendor.has_purchased = has_purchased
        vendor.save()
        
        vendor.tags.set(tag_ids)
        
        # Parse and sync services array (delete and recreate)
        vendor.services.all().delete()
        
        service_names = request.POST.getlist('service_name[]')
        service_descs = request.POST.getlist('service_desc[]')
        service_prices = request.POST.getlist('service_price[]')
        service_notes = request.POST.getlist('service_notes[]')
        
        for i in range(len(service_names)):
            s_name = service_names[i].strip()
            if s_name:
                s_desc = service_descs[i].strip() if i < len(service_descs) else ''
                s_price = service_prices[i].strip() if i < len(service_prices) else ''
                s_note = service_notes[i].strip() if i < len(service_notes) else ''
                VendorService.objects.create(
                    vendor=vendor,
                    name=s_name,
                    description=s_desc,
                    price=s_price,
                    notes=s_note
                )
                
        messages.success(request, f"Vendor '{name}' updated successfully.")
    else:
        messages.error(request, "Failed to update vendor: Name is required.")
        
    return redirect('vendors:vendor_list')


@require_POST
def vendor_delete(request, vendor_id):
    """
    Removes a Vendor record.
    """
    vendor = get_object_or_404(Vendor, pk=vendor_id, business=request.business)
    name = vendor.name
    vendor.delete()
    messages.success(request, f"Vendor '{name}' deleted successfully.")
    return redirect('vendors:vendor_list')


@require_POST
def vendor_pin(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id, business=request.business)
    apply_pin_state(vendor, request.POST.get('pin') == '1')
    return redirect(safe_redirect_target(request, reverse('vendors:vendor_list')))


@require_POST
def vendor_tag_create(request):
    """
    Creates a new dynamic color tag/label representing a product or service category.
    """
    name = request.POST.get('name')
    color = request.POST.get('color', '#6366f1')
    
    if name:
        name = name.strip()
        if color and not color.startswith('#'):
            color = f"#{color}"
            
        tag, created = VendorTag.objects.get_or_create(
            business=request.business,
            name=name,
            defaults={'color': color}
        )
        if created:
            messages.success(request, f"Tag '{name}' created successfully.")
        else:
            messages.info(request, f"Tag '{name}' already exists.")
    else:
        messages.error(request, "Tag Name is required.")
        
    return redirect('vendors:vendor_list')
