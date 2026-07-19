import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.urls import reverse
from core.pinning import apply_pin_state, safe_redirect_target
from documents.views import attachment_payload, create_attachment
from .defaults import ensure_default_task_tags
from .models import Project, TaskList, Task, TaskNote, Tag


def _task_titles_from_list_input(raw_value):
    titles = []
    for line in _clean_empty_list_markers(raw_value).splitlines():
        title = line.strip()
        title = title.lstrip('-*').strip()
        if '. ' in title:
            number, possible_title = title.split('. ', 1)
            if number.isdigit():
                title = possible_title.strip()
        if title:
            titles.append(title[:200])
    return titles


def _clean_empty_list_markers(raw_value):
    cleaned_lines = []
    for line in (raw_value or '').splitlines():
        stripped = line.strip()
        if stripped in {'-', '*'}:
            continue
        if stripped.endswith('.') and stripped[:-1].isdigit():
            continue
        cleaned_lines.append(line.rstrip())
    return '\n'.join(cleaned_lines).strip()


def _project_detail_redirect(project_pk, request=None):
    url = reverse('projects:project_detail', kwargs={'pk': project_pk})
    if request and request.POST.get('return_view') == 'list':
        url = f'{url}#list'
    return redirect(url)

def project_list(request):
    """
    Lists all active projects and workspace folders.
    """
    projects = Project.objects.filter(business=request.business).order_by('-is_pinned', '-pinned_at', '-created_at')
    
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
    # Prefetch task lists and split board cards into active vs completed.
    task_lists = list(project.task_lists.all().prefetch_related('tasks__tags', 'tasks__notes__attachments'))
    for task_list in task_lists:
        tasks = list(task_list.tasks.all())
        task_list.active_tasks = [task for task in tasks if task.status != 'DONE']
        task_list.completed_tasks_count = len(tasks) - len(task_list.active_tasks)
    
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


def task_overview(request, status):
    """
    Shows all pending or completed tasks grouped by their project board.
    """
    list_filter = None
    list_id = request.GET.get('list')
    if list_id:
        list_filter = get_object_or_404(
            TaskList.objects.select_related('project'),
            pk=list_id,
            project__business=request.business,
        )

    if status == 'pending':
        tasks = Task.objects.filter(list__project__business=request.business).exclude(status='DONE')
        page_title = 'Pending Tasks'
        empty_message = 'No pending tasks found.'
        task_status = 'pending'
    elif status == 'completed':
        tasks = Task.objects.filter(list__project__business=request.business, status='DONE')
        page_title = 'Completed Tasks'
        empty_message = 'No completed tasks found.'
        task_status = 'completed'
    else:
        return HttpResponseBadRequest('Unknown task status view.')

    if list_filter:
        tasks = tasks.filter(list=list_filter)
        page_title = f'{page_title}: {list_filter.name}'
        empty_message = f'No {task_status} tasks found in {list_filter.name}.'

    tasks = tasks.select_related('list__project').prefetch_related('notes__attachments').order_by('list__project__name', 'due_date', '-created_at')
    grouped_projects = []
    current_project = None
    current_group = None

    for task in tasks:
        project = task.list.project
        if current_project != project.id:
            current_project = project.id
            current_group = {
                'project': project,
                'tasks': [],
            }
            grouped_projects.append(current_group)
        current_group['tasks'].append(task)

    return render(request, 'projects/task_overview.html', {
        'grouped_projects': grouped_projects,
        'page_title': page_title,
        'empty_message': empty_message,
        'task_status': task_status,
        'list_filter': list_filter,
    })


@require_POST
def project_create(request):
    """
    Creates a new project space in the CRM.
    """
    name = request.POST.get('name')
    description = _clean_empty_list_markers(request.POST.get('description', ''))
    if name:
        project = Project.objects.create(name=name, description=description, business=request.business)
        ensure_default_task_tags(project)
        return redirect('projects:project_detail', pk=project.pk)
    return redirect('projects:project_list')


@require_POST
def project_delete(request, project_id):
    """
    Deletes a project board and its task lists/tasks. Restricted to managers.
    """
    if not request.user.profile.is_manager:
        messages.error(request, "Only managers can delete project boards.")
        return redirect('projects:project_list')

    project = get_object_or_404(Project, pk=project_id, business=request.business)
    project_name = project.name
    project.delete()
    messages.success(request, f"Project board '{project_name}' deleted.")
    return redirect('projects:project_list')


@require_POST
def project_pin(request, project_id):
    project = get_object_or_404(Project, pk=project_id, business=request.business)
    apply_pin_state(project, request.POST.get('pin') == '1')
    return redirect(safe_redirect_target(request, reverse('projects:project_list')))


@require_POST
def task_list_create(request, project_id):
    """
    Creates a new named list column inside a project.
    """
    project = get_object_or_404(Project, pk=project_id, business=request.business)
    name = request.POST.get('name')
    description = _clean_empty_list_markers(request.POST.get('description', ''))
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
    description = _clean_empty_list_markers(request.POST.get('description', ''))
    priority = request.POST.get('priority', 'MEDIUM')
    due_date = request.POST.get('due_date')
    tag_ids = request.POST.getlist('tags')
    
    if not due_date:
        due_date = None
        
    titles = _task_titles_from_list_input(title)
    for task_title in titles:
        task = Task.objects.create(
            list=task_list,
            title=task_title,
            description=description,
            priority=priority,
            due_date=due_date
        )
        if tag_ids:
            task.tags.set(tag_ids)
    return _project_detail_redirect(task_list.project.pk, request)


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
def task_pin(request, task_id):
    task = get_object_or_404(Task, pk=task_id, list__project__business=request.business)
    apply_pin_state(task, request.POST.get('pin') == '1')
    return redirect(safe_redirect_target(request, reverse('projects:project_detail', kwargs={'pk': task.list.project.pk})))


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
    description = _clean_empty_list_markers(request.POST.get('description', ''))
    priority = request.POST.get('priority')
    status = request.POST.get('status')
    due_date = request.POST.get('due_date')
    list_id = request.POST.get('list')
    tag_ids = request.POST.getlist('tags')
    note_updates = []
    for key, value in request.POST.items():
        if key.startswith('note_content_'):
            note_id = key.removeprefix('note_content_')
            if note_id.isdigit():
                note_updates.append((int(note_id), _clean_empty_list_markers(value)))
    new_note_content = _clean_empty_list_markers(request.POST.get('new_note_content', ''))
    note_attachment_files = {}
    for key, files in request.FILES.lists():
        if key.startswith('note_attachments_'):
            note_id = key.removeprefix('note_attachments_')
            if note_id.isdigit():
                note_attachment_files[int(note_id)] = files
    
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
        for note_id, note_content in note_updates:
            note = TaskNote.objects.filter(pk=note_id, task=task).first()
            if note and note_content:
                note.content = note_content
                note.save(update_fields=['content'])
                for file_obj in note_attachment_files.get(note_id, []):
                    create_attachment(
                        business=request.business,
                        uploaded_by=request.user,
                        file_obj=file_obj,
                        task_note=note,
                    )
        if new_note_content:
            note = TaskNote.objects.create(task=task, content=new_note_content)
            for file_obj in request.FILES.getlist('new_note_attachments'):
                create_attachment(
                    business=request.business,
                    uploaded_by=request.user,
                    file_obj=file_obj,
                    task_note=note,
                )
        messages.success(request, f"Task '{title}' updated successfully.")
    return _project_detail_redirect(task.list.project.pk, request)


@require_POST
def task_note_create(request, task_id):
    """
    Appends a new timestamped follow-up note/comment to a task.
    """
    task = get_object_or_404(Task, pk=task_id, list__project__business=request.business)
    content = _clean_empty_list_markers(request.POST.get('content', ''))
    if content:
        note = TaskNote.objects.create(task=task, content=content)
        [
            create_attachment(
                business=request.business,
                uploaded_by=request.user,
                file_obj=file_obj,
                task_note=note,
            )
            for file_obj in request.FILES.getlist('attachments')
        ]
        attachments = note.attachments.all()
        messages.success(request, "Follow-up note added.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'note': {
                    'id': note.id,
                    'content': note.content,
                    'date': note.created_at.strftime('%b %d, %Y, %I:%M %p'),
                    'attachments': [attachment_payload(attachment) for attachment in attachments],
                },
            })
    elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Follow-up note cannot be blank.'}, status=400)
    return redirect('projects:project_detail', pk=task.list.project.pk)


@require_POST
def task_note_update(request, note_id):
    note = get_object_or_404(TaskNote, pk=note_id, task__list__project__business=request.business)
    content = _clean_empty_list_markers(request.POST.get('content', ''))
    if content:
        note.content = content
        note.save(update_fields=['content'])
        [
            create_attachment(
                business=request.business,
                uploaded_by=request.user,
                file_obj=file_obj,
                task_note=note,
            )
            for file_obj in request.FILES.getlist('attachments')
        ]
        attachments = note.attachments.all()
        messages.success(request, "Follow-up note updated.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'note': {
                    'id': note.id,
                    'content': note.content,
                    'date': note.created_at.strftime('%b %d, %Y, %I:%M %p'),
                    'attachments': [attachment_payload(attachment) for attachment in attachments],
                },
            })
    else:
        messages.error(request, "Follow-up note cannot be blank.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Follow-up note cannot be blank.'}, status=400)
    return _project_detail_redirect(note.task.list.project.pk, request)


@require_POST
def task_note_delete(request, note_id):
    note = get_object_or_404(TaskNote, pk=note_id, task__list__project__business=request.business)
    project_pk = note.task.list.project.pk
    note.delete()
    messages.success(request, "Follow-up note deleted.")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'note_id': note_id})
    return _project_detail_redirect(project_pk, request)


@require_POST
def task_quick_add(request, project_id):
    """
    Quick checklist entry. Automatically hooks tasks to a default workspace list column.
    """
    project = get_object_or_404(Project, pk=project_id, business=request.business)
    title = request.POST.get('title')
    titles = _task_titles_from_list_input(title)
    if titles:
        # Fetch first column. If none exists, auto-spawn 'Main Checklist'
        task_list = project.task_lists.first()
        if not task_list:
            task_list = TaskList.objects.create(
                project=project, 
                name="Main Checklist", 
                description="Default checklist category for quick entries."
            )

        for task_title in titles:
            Task.objects.create(
                list=task_list,
                title=task_title,
                priority="MEDIUM",
                status="TODO"
            )
        messages.success(request, f"Added {len(titles)} checklist item{'s' if len(titles) != 1 else ''}.")
        
    return _project_detail_redirect(project_id, request)


@require_POST
def task_list_update(request, list_id):
    """
    Modifies list column title or description metadata.
    """
    task_list = get_object_or_404(TaskList, pk=list_id, project__business=request.business)
    name = request.POST.get('name')
    description = _clean_empty_list_markers(request.POST.get('description', ''))
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
