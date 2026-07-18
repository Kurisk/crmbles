import re

from django.db import models


URL_PATTERN = re.compile(r"https?://[^\s<>()]+")


class Project(models.Model):
    """
    Represents an overarching business initiative or workspace target
    (e.g., the 'dowitz' project).
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    ]

    name = models.CharField(max_length=100)
    business = models.ForeignKey('accounts.Business', related_name='projects', on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    Vibrant colored labels/tags used to categorize tasks visually.
    """
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6366f1') # hex code (e.g. #ec4899)
    project = models.ForeignKey(Project, related_name='tags', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('name', 'project')

    def __str__(self):
        return f"{self.project.name} - {self.name}"



class TaskList(models.Model):
    """
    Groups specific workflows or task scopes inside a Project
    (e.g., 'Marketing Tasks', 'Technical Architecture').
    """
    project = models.ForeignKey(Project, related_name='task_lists', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class Task(models.Model):
    """
    An individual, trackable item of work. Features priority categories,
    status tracking (To-Do, Progress, Done), and deadlines.
    """
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]

    list = models.ForeignKey(TaskList, related_name='tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    due_date = models.DateField(null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True, related_name='tasks')
    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-pinned_at', 'due_date', 'created_at']

    def __str__(self):
        return self.title

    @property
    def latest_note(self):
        notes = self._prefetched_notes()
        return notes[-1] if notes else None

    @property
    def notes_for_cards(self):
        return self._prefetched_notes()

    @property
    def extracted_links(self):
        return [link["url"] for link in self.link_previews]

    @property
    def link_previews(self):
        seen = set()
        links = []
        sources = [{"content": self.description, "label": "Task description", "note": None}]
        sources.extend(
            {
                "content": note.content,
                "label": f"Note {index}",
                "note": note,
            }
            for index, note in enumerate(self._prefetched_notes(), start=1)
        )
        for source in sources:
            value = source["content"]
            for match in URL_PATTERN.findall(value or ""):
                url = match.rstrip(".,);]")
                if url and url not in seen:
                    seen.add(url)
                    links.append({
                        "url": url,
                        "source_label": source["label"],
                        "source_note": source["note"],
                    })
        return links

    def _prefetched_notes(self):
        if not hasattr(self, "_notes_cache_for_cards"):
            self._notes_cache_for_cards = list(self.notes.all())
        return self._notes_cache_for_cards


class TaskNote(models.Model):
    """
    Timeline comments and follow-up notes associated with a Task.
    """
    task = models.ForeignKey(Task, related_name='notes', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Note on {self.task.title} at {self.created_at}"
