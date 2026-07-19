import markdown
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from core.pinning import apply_pin_state, safe_redirect_target
from .models import Document, DocumentAttachment
from projects.models import Project


def create_attachment(*, business, uploaded_by, file_obj, title='', document=None, task_note=None):
    return DocumentAttachment.objects.create(
        business=business,
        uploaded_by=uploaded_by if uploaded_by.is_authenticated else None,
        document=document,
        task_note=task_note,
        title=title.strip(),
        file=file_obj,
        original_filename=file_obj.name,
        content_type=getattr(file_obj, 'content_type', '') or '',
        size=getattr(file_obj, 'size', 0) or 0,
    )


def attachment_payload(attachment):
    return {
        'id': attachment.id,
        'name': attachment.display_name,
        'filename': attachment.original_filename,
        'url': attachment.file.url,
        'size': attachment.size_label,
        'extension': attachment.extension.upper(),
        'created': attachment.created_at.strftime('%b %d, %Y, %I:%M %p'),
    }

def document_list(request):
    """
    Renders all saved wiki articles, design documents, and ideas.
    """
    documents = Document.objects.filter(business=request.business).order_by('-is_pinned', '-pinned_at', '-updated_at')
    attachments = DocumentAttachment.objects.filter(
        business=request.business,
        document__isnull=True,
        task_note__isnull=True,
    ).select_related('uploaded_by')
    return render(request, 'documents/document_list.html', {
        'documents': documents,
        'attachments': attachments,
    })


def document_detail(request, pk):
    """
    Server-renders a Document, converting Markdown elements into safe HTML code
    for high-fidelity premium viewing. Parses task lists dynamically.
    """
    document = get_object_or_404(
        Document.objects.prefetch_related('attachments'),
        pk=pk,
        business=request.business,
    )
    
    # Pre-parse task items [ ] and [x] to render styled, interactive checkboxes
    raw_content = document.content
    lines = raw_content.split('\n')
    processed_lines = []
    idx = 0
    for line in lines:
        if '[ ]' in line:
            line = line.replace('[ ]', f'<input type="checkbox" class="task-toggle-checkbox doc-checklist-checkbox" data-idx="{idx}" onclick="toggleDocChecklist(this)" style="display: inline-block; vertical-align: middle; margin-right: 8px;">')
            idx += 1
        elif '[x]' in line:
            line = line.replace('[x]', f'<input type="checkbox" class="task-toggle-checkbox doc-checklist-checkbox" checked data-idx="{idx}" onclick="toggleDocChecklist(this)" style="display: inline-block; vertical-align: middle; margin-right: 8px;">')
            idx += 1
        processed_lines.append(line)
        
    processed_content = '\n'.join(processed_lines)
    
    # Compile markdown content into HTML with support for tables and code blocks
    compiled_html = markdown.markdown(
        processed_content,
        extensions=['fenced_code', 'tables', 'nl2br', 'toc']
    )
    
    context = {
        'document': document,
        'compiled_html': mark_safe(compiled_html)
    }
    return render(request, 'documents/document_detail.html', context)


def document_create(request):
    """
    Handles drawing and submitting the note creation screen.
    Includes live side-by-side preview panel variables.
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content', '')
        project_id = request.POST.get('project')
        
        project = None
        if project_id:
            project = get_object_or_404(Project, pk=project_id, business=request.business)
            
        if title:
            doc = Document.objects.create(
                title=title,
                content=content,
                project=project,
                business=request.business
            )
            messages.success(request, f"Document '{title}' created successfully.")
            return redirect('documents:document_detail', pk=doc.pk)
        else:
            messages.error(request, "A document title is required.")
            
    projects = Project.objects.filter(business=request.business)
    return render(request, 'documents/document_form.html', {
        'projects': projects,
        'is_create': True
    })


def document_update(request, pk):
    """
    Modifies an existing Markdown document.
    """
    document = get_object_or_404(Document, pk=pk, business=request.business)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content', '')
        project_id = request.POST.get('project')
        
        project = None
        if project_id:
            project = get_object_or_404(Project, pk=project_id, business=request.business)
            
        if title:
            document.title = title
            document.content = content
            document.project = project
            document.save()
            messages.success(request, f"Document '{title}' updated successfully.")
            return redirect('documents:document_detail', pk=document.pk)
        else:
            messages.error(request, "A document title is required.")
            
    projects = Project.objects.filter(business=request.business)
    return render(request, 'documents/document_form.html', {
        'document': document,
        'projects': projects,
        'is_create': False
    })


def document_delete(request, pk):
    """
    Deletes a specific note space.
    """
    if request.method == 'POST':
        document = get_object_or_404(Document, pk=pk, business=request.business)
        title = document.title
        document.delete()
        messages.success(request, f"Document '{title}' deleted successfully.")
    return redirect('documents:document_list')


@require_POST
def document_pin(request, pk):
    document = get_object_or_404(Document, pk=pk, business=request.business)
    apply_pin_state(document, request.POST.get('pin') == '1')
    return redirect(safe_redirect_target(request, reverse('documents:document_list')))


@require_POST
def document_checklist_toggle(request, pk):
    """
    AJAX endpoint to toggle a checklist checkbox item directly inside a Document.
    """
    document = get_object_or_404(Document, pk=pk, business=request.business)
    try:
        data = json.loads(request.body)
        target_idx = int(data.get('index'))
        is_checked = bool(data.get('checked'))
        
        lines = document.content.split('\n')
        current_idx = 0
        for i, line in enumerate(lines):
            # Check for checklists
            if '[ ]' in line or '[x]' in line:
                if current_idx == target_idx:
                    if is_checked:
                        lines[i] = line.replace('[ ]', '[x]')
                    else:
                        lines[i] = line.replace('[x]', '[ ]')
                    break
                current_idx += 1
                
        document.content = '\n'.join(lines)
        document.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def attachment_upload(request):
    files = request.FILES.getlist('files')
    title = request.POST.get('title', '')
    if not files:
        messages.error(request, "Choose at least one file to upload.")
        return redirect('documents:document_list')

    for file_obj in files:
        create_attachment(
            business=request.business,
            uploaded_by=request.user,
            file_obj=file_obj,
            title=title if len(files) == 1 else '',
        )
    messages.success(request, f"Uploaded {len(files)} file{'s' if len(files) != 1 else ''}.")
    return redirect('documents:document_list')


@require_POST
def attachment_delete(request, attachment_id):
    attachment = get_object_or_404(DocumentAttachment, pk=attachment_id, business=request.business)
    attachment.file.delete(save=False)
    attachment.delete()
    messages.success(request, "File attachment deleted.")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'attachment_id': attachment_id})
    return redirect(safe_redirect_target(request, reverse('documents:document_list')))
