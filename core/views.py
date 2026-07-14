from django.shortcuts import render
from projects.models import Project, Task
from documents.models import Document
from finance.models import Expense, Invoice

def dashboard(request):
    """
    Renders the primary CRM workspace hub showing database metrics,
    upcoming active tasks, and recent document sheets.
    """
    if not request.user.is_authenticated:
        return render(request, 'core/welcome.html')

    business = request.business
    projects = Project.objects.filter(business=business)
    tasks = Task.objects.filter(list__project__business=business)
    documents = Document.objects.filter(business=business)
    invoices = Invoice.objects.filter(business=business)
    expenses = Expense.objects.filter(business=business)
    total_projects = projects.count()
    pending_tasks_count = tasks.exclude(status='DONE').count()
    completed_tasks_count = tasks.filter(status='DONE').count()
    total_tasks = tasks.count()
    total_documents = documents.count()
    pending_invoices_count = invoices.exclude(status='PAID').count()
    pending_expenses_count = expenses.filter(status='PENDING').count()
    
    # Grab most recent modified documentation sheets
    recent_documents = documents.order_by('-updated_at')[:4]
    
    # Grab outstanding tasks prioritizing near due dates and recent urgency
    recent_tasks = tasks.exclude(status='DONE').order_by('due_date', '-created_at')[:5]
    
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
