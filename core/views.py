from django.shortcuts import render
from projects.models import Project, Task
from documents.models import Document
from finance.models import Expense, Invoice
from .product_info import FAQ_SECTIONS


def _dashboard_feature_access(request):
    profile = request.user.profile
    business = request.business
    membership = None
    if business and not profile.is_manager:
        membership = request.user.business_memberships.filter(business=business).first()

    access = {}
    for feature in ("projects", "documents", "vendors", "clients", "finance", "manage_accounts"):
        if feature == "manage_accounts":
            access[feature] = profile.is_manager
        else:
            access[feature] = profile.is_manager or (membership and membership.can_access(feature)) or (business is None and profile.can_access(feature))
    return access


def dashboard(request):
    """
    Renders the primary CRM workspace hub showing database metrics,
    upcoming active tasks, and recent document sheets.
    """
    if not request.user.is_authenticated:
        return render(request, 'core/welcome.html')

    business = request.business
    feature_access = _dashboard_feature_access(request)
    projects = Project.objects.filter(business=business) if feature_access["projects"] else Project.objects.none()
    tasks = Task.objects.filter(list__project__business=business) if feature_access["projects"] else Task.objects.none()
    documents = Document.objects.filter(business=business) if feature_access["documents"] else Document.objects.none()
    invoices = Invoice.objects.filter(business=business) if feature_access["finance"] else Invoice.objects.none()
    expenses = Expense.objects.filter(business=business) if feature_access["finance"] else Expense.objects.none()
    total_projects = projects.count()
    pending_tasks_count = tasks.exclude(status='DONE').count()
    completed_tasks_count = tasks.filter(status='DONE').count()
    total_tasks = tasks.count()
    total_documents = documents.count()
    pending_invoices_count = invoices.exclude(status='PAID').count()
    pending_expenses_count = expenses.filter(status='PENDING').count()
    
    # Grab most recent modified documentation sheets
    recent_documents = documents.order_by('-is_pinned', '-pinned_at', '-updated_at')[:4]
    
    # Grab outstanding tasks prioritizing near due dates and recent urgency
    recent_tasks = tasks.exclude(status='DONE').order_by('-is_pinned', '-pinned_at', 'due_date', '-created_at')[:5]
    
    # Calculate percentage progress for Dowitz projects overall
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = int((completed_tasks_count / total_tasks) * 100)
        
    context = {
        'total_projects': total_projects,
        'pending_tasks_count': pending_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'total_tasks': total_tasks,
        'total_documents': total_documents,
        'pending_invoices_count': pending_invoices_count,
        'pending_expenses_count': pending_expenses_count,
        'recent_documents': recent_documents,
        'recent_tasks': recent_tasks,
        'completion_rate': completion_rate,
    }
    return render(request, 'core/dashboard.html', context)


def faq(request):
    return render(request, 'core/faq.html', {"faq_sections": FAQ_SECTIONS})


def latest_update(request):
    return render(request, 'core/latest_update.html')
