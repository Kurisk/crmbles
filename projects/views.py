import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from .models import Project, TaskList, Task, TaskNote, Tag

def project_list(request):
    """
    Lists all active projects and workspace folders.
    """
    projects = Project.objects.filter(business=request.business).order_by('-created_at')
    
    # Calculate statistics for each project
    project_stats = []
    for project in projects:
        total_tasks = Task.objects.filter(list__project=project).count()
        completed_tasks = Task.objects.filter(list__project=project, status='DONE').count()
        completion_rate = 0
        if total_tasks > 0:
            completion_rate = int((completed_tasks / total_tasks) * 100)
            
        project_stats.append({
            'project': project,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': completion_rate
        })
        
    return render(request, 'projects/project_list.html', {'project_stats': project_stats})


def project_detail(request, pk):
    """
    Detailed workspace dashboard for a specific project.
    Groups tasks by custom TaskLists and handles task additions.
    """
    project = get_object_or_404(Project, pk=pk, business=request.business)
    # Prefetch task lists and their tasks
    task_lists = project.task_lists.all().prefetch_related('tasks__tags', 'tasks__notes')
    
    # Calculate general metrics
    total_tasks = Task.objects.filter(list__project=project).count()
    completed_tasks = Task.objects.filter(list__project=project, status='DONE').count()
    pending_tasks = total_tasks - completed_tasks
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = int((completed_tasks / total_tasks) * 100)
        
    # Fetch all project tags and active tags that are associated with at least one task
    all_tags = project.tags.all()
    active_tags = all_tags.filter(tasks__isnull=False).distinct()
    
    context = {
        'project': project,
        'task_lists': task_lists,
        'tags': all_tags,
        'active_tags': active_tags,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'completion_rate': completion_rate
    }
    return render(request, 'projects/project_detail.html', context)


@require_POST
def project_create(request):
    """
    Creates a new project space in the CRM.
    """
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    if name:
        project = Project.objects.create(name=name, description=description, business=request.business)
        return redirect('projects:project_detail', pk=project.pk)
    return redirect('projects:project_list')


@require_POST
def task_list_create(request, project_id):
    """
    Creates a new named list column inside a project.
    """
    project = get_object_or_404(Project, pk=project_id, business=request.business)
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    if name:
        TaskList.objects.create(project=project, name=name, description=description)
    return redirect('projects:project_detail', pk=project.pk)


@require_POST
def task_create(request, list_id):
    """
    Creates a new specific Task inside a TaskList.
    """
    task_list = get_object_or_404(TaskList, pk=list_id, project__business=request.business)
    title = request.POST.get('title')
    description = request.POST.get('description', '')
    priority = request.POST.get('priority', 'MEDIUM')
    due_date = request.POST.get('due_date')
    tag_ids = request.POST.getlist('tags')
    
    if not due_date:
        due_date = None
        
    if title:
        task = Task.objects.create(
            list=task_list,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date
        )
        if tag_ids:
            task.tags.set(tag_ids)
    return redirect('projects:project_detail', pk=task_list.project.pk)


@require_POST
def task_toggle(request, task_id):
    """
    AJAX endpoint to toggle a Task's status between 'TODO' and 'DONE'.
    """
    task = get_object_or_404(Task, pk=task_id, list__project__business=request.business)
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        if new_status in ['TODO', 'PROGRESS', 'DONE']:
            task.status = new_status
            task.save()
            return JsonResponse({'success': True, 'status': task.status})
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def task_delete(request, task_id):
    """
    Removes a Task item.
    """
    task = get_object_or_404(Task, pk=task_id, list__project__business=request.business)
    project_pk = task.list.project.pk
    task.delete()
    return redirect('projects:project_detail', pk=project_pk)


@require_POST
def task_update(request, task_id):
    """
    Updates details for a specific Task (Title, Desc, Priority, Status, Due Date, List, Tags).
    """
    task = get_object_or_404(Task, pk=task_id, list__project__business=request.business)
    title = request.POST.get('title')
    description = request.POST.get('description', '')
    priority = request.POST.get('priority')
    status = request.POST.get('status')
    due_date = request.POST.get('due_date')
    list_id = request.POST.get('list')
    tag_ids = request.POST.getlist('tags')
    
    if not due_date:
        due_date = None
        
    if title:
        task.title = title
        task.description = description
        if priority in ['LOW', 'MEDIUM', 'HIGH']:
            task.priority = priority
        if status in ['TODO', 'PROGRESS', 'DONE']:
            task.status = status
        task.due_date = due_date
        
        if list_id:
            task_list = get_object_or_404(TaskList, pk=list_id, project=task.list.project, project__business=request.business)
            task.list = task_list
            
        task.save()
        task.tags.set(tag_ids)
        messages.success(request, f"Task '{title}' updated successfully.")
    return redirect('projects:project_detail', pk=task.list.project.pk)


@require_POST
def task_note_create(request, task_id):
    """
    Appends a new timestamped follow-up note/comment to a task.
    """
    task = get_object_or_404(Task, pk=task_id, list__project__business=request.business)
    content = request.POST.get('content')
    if content:
        TaskNote.objects.create(task=task, content=content)
        messages.success(request, "Follow-up note added.")
    return redirect('projects:project_detail', pk=task.list.project.pk)


@require_POST
def task_quick_add(request, project_id):
    """
    Quick checklist entry. Automatically hooks tasks to a default workspace list column.
    """
    project = get_object_or_404(Project, pk=project_id, business=request.business)
    title = request.POST.get('title')
    if title:
        # Fetch first column. If none exists, auto-spawn 'Main Checklist'
        task_list = project.task_lists.first()
        if not task_list:
            task_list = TaskList.objects.create(
                project=project, 
                name="Main Checklist", 
                description="Default checklist category for quick entries."
            )
            
        Task.objects.create(
            list=task_list,
            title=title,
            priority="MEDIUM",
            status="TODO"
        )
        messages.success(request, f"Added checklist item: '{title}'")
        
    return redirect(f'/projects/{project_id}/#list')


@require_POST
def task_list_update(request, list_id):
    """
    Modifies list column title or description metadata.
    """
    task_list = get_object_or_404(TaskList, pk=list_id, project__business=request.business)
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    if name:
        task_list.name = name
        task_list.description = description
        task_list.save()
        messages.success(request, f"List '{name}' updated successfully.")
    return redirect('projects:project_detail', pk=task_list.project.pk)


@require_POST
def task_list_delete(request, list_id):
    """
    Removes a list column and cascade-deletes all child tasks.
    """
    task_list = get_object_or_404(TaskList, pk=list_id, project__business=request.business)
    project_pk = task_list.project.pk
    list_name = task_list.name
    task_list.delete()
    messages.success(request, f"List '{list_name}' deleted successfully.")
    return redirect('projects:project_detail', pk=project_pk)


@require_POST
def tag_create(request, project_id):
    """
    Creates a new custom named tag with a specific hex color code for a project workspace.
    """
    project = get_object_or_404(Project, pk=project_id, business=request.business)
    name = request.POST.get('name')
    color = request.POST.get('color', '#6366f1')
    
    if name:
        name = name.strip()
        if color and not color.startswith('#'):
            color = f"#{color}"
            
        tag, created = Tag.objects.get_or_create(
            project=project,
            name=name,
            defaults={'color': color}
        )
        if created:
            messages.success(request, f"Tag '{name}' created successfully.")
        else:
            messages.info(request, f"Tag '{name}' already exists.")
            
    return redirect('projects:project_detail', pk=project.pk)
