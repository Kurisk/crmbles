from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from decimal import Decimal, InvalidOperation
from projects.models import Project
from vendors.models import Vendor
from .models import Invoice, InvoiceLineItem, Expense, ExpenseLineItem, CapitalInjection, ExpenseCategory, IndustryExpenseItem


def _line_items_from_post(request):
    items = []
    names = request.POST.getlist('line_item_name[]')
    amounts = request.POST.getlist('line_item_amount[]')
    for index, name in enumerate(names):
        clean_name = name.strip()
        amount_value = amounts[index].strip() if index < len(amounts) else ''
        if not clean_name and not amount_value:
            continue
        if not clean_name or not amount_value:
            continue
        try:
            amount = Decimal(amount_value)
        except (InvalidOperation, TypeError):
            continue
        if amount < 0:
            continue
        items.append({'name': clean_name, 'amount': amount})
    return items


def _amount_from_post_or_items(request, field_name='amount'):
    items = _line_items_from_post(request)
    if items:
        return sum((item['amount'] for item in items), Decimal('0.00')), items
    amount = request.POST.get(field_name) or '0'
    try:
        return Decimal(amount), items
    except (InvalidOperation, TypeError):
        return Decimal('0.00'), items


def _sync_invoice_line_items(invoice, items):
    invoice.line_items.all().delete()
    InvoiceLineItem.objects.bulk_create([
        InvoiceLineItem(invoice=invoice, name=item['name'], amount=item['amount'])
        for item in items
    ])


def _sync_expense_line_items(expense, items):
    expense.line_items.all().delete()
    ExpenseLineItem.objects.bulk_create([
        ExpenseLineItem(expense=expense, name=item['name'], amount=item['amount'])
        for item in items
    ])

def finance_dashboard(request):
    business = request.business
    # Aggregations
    invoice_base = Invoice.objects.filter(business=business)
    expense_base = Expense.objects.filter(business=business)
    total_invoiced = invoice_base.aggregate(total=Sum('amount'))['total'] or 0
    total_collected = invoice_base.filter(status='PAID').aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = expense_base.aggregate(total=Sum('amount'))['total'] or 0
    net_profit = total_collected - total_expenses

    injected_capital = CapitalInjection.objects.filter(business=business).aggregate(total=Sum('amount'))['total'] or 0
    # For loans that are not repaid
    outstanding_loans = CapitalInjection.objects.filter(business=business, injection_type='LOAN', is_repaid=False).aggregate(total=Sum('amount'))['total'] or 0

    # Lists
    invoice_query = request.GET.get('invoice_q', '').strip()
    invoices = invoice_base.select_related('project', 'vendor').prefetch_related('line_items')
    if invoice_query:
        invoices = invoices.filter(
            Q(client_name__icontains=invoice_query) |
            Q(title__icontains=invoice_query) |
            Q(notes__icontains=invoice_query) |
            Q(project__name__icontains=invoice_query) |
            Q(vendor__name__icontains=invoice_query)
        )
    expenses = expense_base.select_related('vendor', 'category', 'industry_item').prefetch_related('line_items')
    injections = CapitalInjection.objects.filter(business=business)
    all_categories = ExpenseCategory.objects.filter(business=business)
    industry_items = IndustryExpenseItem.objects.filter(business=business).select_related('category')

    # Help dynamic dropdown selections in modal creation
    all_projects = Project.objects.filter(business=business)
    all_vendors = Vendor.objects.filter(business=business).prefetch_related('services')

    # Dynamic Choice list representations
    injection_types = CapitalInjection.TYPE_CHOICES
    invoice_statuses = Invoice.STATUS_CHOICES

    context = {
        'total_invoiced': total_invoiced,
        'total_collected': total_collected,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'injected_capital': injected_capital,
        'outstanding_loans': outstanding_loans,
        
        'invoices': invoices,
        'invoice_query': invoice_query,
        'expenses': expenses,
        'injections': injections,
        'all_categories': all_categories,
        'industry_items': industry_items,
        
        'all_projects': all_projects,
        'all_vendors': all_vendors,
        'injection_types': injection_types,
        'invoice_statuses': invoice_statuses,
    }
    return render(request, 'finance/finance_dashboard.html', context)

# Category CRUD
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color', '#6366f1')
        if name:
            ExpenseCategory.objects.get_or_create(business=request.business, name=name.strip(), defaults={'color': color})
            messages.success(request, f"Expense category '{name}' has been created.")
    return redirect('finance:dashboard')


def _manager_required(request):
    return request.user.profile.is_manager


def industry_item_create(request):
    if request.method == 'POST':
        if not _manager_required(request):
            messages.error(request, "Only managers can manage expense setup items.")
            return redirect('finance:dashboard')
        industry = request.POST.get('industry', '').strip()
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        default_notes = request.POST.get('default_notes', '')
        is_active = 'is_active' in request.POST
        category = None
        if category_id:
            category = get_object_or_404(ExpenseCategory, pk=category_id, business=request.business)
        if industry and name:
            IndustryExpenseItem.objects.update_or_create(
                business=request.business,
                industry=industry,
                name=name,
                defaults={
                    'category': category,
                    'default_notes': default_notes,
                    'is_active': is_active,
                }
            )
            messages.success(request, f"Expense setup item '{name}' saved.")
        else:
            messages.error(request, "Industry and item name are required.")
    return redirect('finance:dashboard')


def industry_item_update(request, pk):
    item = get_object_or_404(IndustryExpenseItem, pk=pk, business=request.business)
    if request.method == 'POST':
        if not _manager_required(request):
            messages.error(request, "Only managers can manage expense setup items.")
            return redirect('finance:dashboard')
        category_id = request.POST.get('category')
        item.industry = request.POST.get('industry', '').strip()
        item.name = request.POST.get('name', '').strip()
        item.default_notes = request.POST.get('default_notes', '')
        item.is_active = 'is_active' in request.POST
        item.category = get_object_or_404(ExpenseCategory, pk=category_id, business=request.business) if category_id else None
        if item.industry and item.name:
            item.save()
            messages.success(request, f"Expense setup item '{item.name}' updated.")
        else:
            messages.error(request, "Industry and item name are required.")
    return redirect('finance:dashboard')


def industry_item_delete(request, pk):
    item = get_object_or_404(IndustryExpenseItem, pk=pk, business=request.business)
    if request.method == 'POST':
        if not _manager_required(request):
            messages.error(request, "Only managers can manage expense setup items.")
            return redirect('finance:dashboard')
        name = item.name
        item.delete()
        messages.success(request, f"Expense setup item '{name}' deleted.")
    return redirect('finance:dashboard')

# Invoice CRUD
def invoice_create(request):
    if request.method == 'POST':
        client_name = request.POST.get('client_name')
        title = request.POST.get('title')
        project_id = request.POST.get('project')
        vendor_id = request.POST.get('vendor')
        amount, line_items = _amount_from_post_or_items(request)
        invoice_date = request.POST.get('invoice_date')
        due_date = request.POST.get('due_date') or None
        status = request.POST.get('status', 'SENT')
        notes = request.POST.get('notes', '')

        project = None
        if project_id:
            project = get_object_or_404(Project, pk=project_id, business=request.business)

        vendor = None
        if vendor_id:
            vendor = get_object_or_404(Vendor, pk=vendor_id, business=request.business)

        invoice = Invoice.objects.create(
            client_name=client_name,
            title=title,
            business=request.business,
            project=project,
            vendor=vendor,
            amount=amount,
            invoice_date=invoice_date,
            due_date=due_date,
            status=status,
            notes=notes
        )
        _sync_invoice_line_items(invoice, line_items)
        messages.success(request, f"Invoice for {client_name} was successfully created.")
    return redirect('finance:dashboard')

def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, business=request.business)
    if request.method == 'POST':
        invoice.client_name = request.POST.get('client_name')
        invoice.title = request.POST.get('title')
        project_id = request.POST.get('project')
        vendor_id = request.POST.get('vendor')
        invoice.amount, line_items = _amount_from_post_or_items(request)
        invoice.invoice_date = request.POST.get('invoice_date')
        invoice.due_date = request.POST.get('due_date') or None
        invoice.status = request.POST.get('status')
        invoice.notes = request.POST.get('notes', '')

        if project_id:
            invoice.project = get_object_or_404(Project, pk=project_id, business=request.business)
        else:
            invoice.project = None

        if vendor_id:
            invoice.vendor = get_object_or_404(Vendor, pk=vendor_id, business=request.business)
        else:
            invoice.vendor = None

        invoice.save()
        _sync_invoice_line_items(invoice, line_items)
        messages.success(request, f"Invoice for {invoice.client_name} was successfully saved.")
    return redirect('finance:dashboard')

def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, business=request.business)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, "Invoice was successfully deleted.")
    return redirect('finance:dashboard')

# Expense CRUD
def expense_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        amount, line_items = _amount_from_post_or_items(request)
        expense_date = request.POST.get('expense_date')
        category_id = request.POST.get('category')
        industry_item_id = request.POST.get('industry_item')
        status = request.POST.get('status', 'PAID')
        notes = request.POST.get('notes', '')
        
        vendor_id = request.POST.get('vendor')
        vendor_name_fallback = request.POST.get('vendor_name_fallback', '')

        vendor = None
        if vendor_id:
            vendor = get_object_or_404(Vendor, pk=vendor_id, business=request.business)

        category = None
        if category_id:
            category = get_object_or_404(ExpenseCategory, pk=category_id, business=request.business)

        industry_item = None
        if industry_item_id:
            industry_item = get_object_or_404(IndustryExpenseItem, pk=industry_item_id, business=request.business)
            if category is None:
                category = industry_item.category

        if category is None and vendor and vendor.default_expense_category:
            category = vendor.default_expense_category

        expense = Expense.objects.create(
            title=title,
            business=request.business,
            industry_item=industry_item,
            amount=amount,
            expense_date=expense_date,
            category=category,
            status=status,
            notes=notes,
            vendor=vendor,
            vendor_name_fallback=vendor_name_fallback
        )
        _sync_expense_line_items(expense, line_items)
        messages.success(request, f"Expense '{title}' was successfully recorded.")
    return redirect('finance:dashboard')

def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk, business=request.business)
    if request.method == 'POST':
        expense.title = request.POST.get('title')
        industry_item_id = request.POST.get('industry_item')
        expense.amount, line_items = _amount_from_post_or_items(request)
        expense.expense_date = request.POST.get('expense_date')
        category_id = request.POST.get('category')
        expense.status = request.POST.get('status')
        expense.notes = request.POST.get('notes', '')
        
        vendor_id = request.POST.get('vendor')
        expense.vendor_name_fallback = request.POST.get('vendor_name_fallback', '')

        if vendor_id:
            expense.vendor = get_object_or_404(Vendor, pk=vendor_id, business=request.business)
        else:
            expense.vendor = None

        if category_id:
            expense.category = get_object_or_404(ExpenseCategory, pk=category_id, business=request.business)
        else:
            expense.category = None

        if industry_item_id:
            expense.industry_item = get_object_or_404(IndustryExpenseItem, pk=industry_item_id, business=request.business)
            if expense.category is None:
                expense.category = expense.industry_item.category
        else:
            expense.industry_item = None

        if expense.category is None and expense.vendor and expense.vendor.default_expense_category:
            expense.category = expense.vendor.default_expense_category

        expense.save()
        _sync_expense_line_items(expense, line_items)
        messages.success(request, f"Expense '{expense.title}' was successfully updated.")
    return redirect('finance:dashboard')

def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, business=request.business)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, "Expense was successfully removed.")
    return redirect('finance:dashboard')

# Capital Injection CRUD
def injection_create(request):
    if request.method == 'POST':
        source = request.POST.get('source')
        injection_type = request.POST.get('injection_type', 'LOAN')
        amount = request.POST.get('amount')
        injection_date = request.POST.get('injection_date')
        notes = request.POST.get('notes', '')
        is_repaid = request.POST.get('is_repaid') == 'true'

        CapitalInjection.objects.create(
            source=source,
            business=request.business,
            injection_type=injection_type,
            amount=amount,
            injection_date=injection_date,
            notes=notes,
            is_repaid=is_repaid
        )
        messages.success(request, f"Capital injection from {source} was successfully created.")
    return redirect('finance:dashboard')

def injection_update(request, pk):
    injection = get_object_or_404(CapitalInjection, pk=pk, business=request.business)
    if request.method == 'POST':
        injection.source = request.POST.get('source')
        injection.injection_type = request.POST.get('injection_type')
        injection.amount = request.POST.get('amount')
        injection.injection_date = request.POST.get('injection_date')
        injection.notes = request.POST.get('notes', '')
        injection.is_repaid = request.POST.get('is_repaid') == 'true'

        injection.save()
        messages.success(request, f"Capital injection from {injection.source} was updated.")
    return redirect('finance:dashboard')

def injection_delete(request, pk):
    injection = get_object_or_404(CapitalInjection, pk=pk, business=request.business)
    if request.method == 'POST':
        injection.delete()
        messages.success(request, "Capital injection was successfully removed.")
    return redirect('finance:dashboard')
