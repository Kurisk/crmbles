from django.db import models


class ClientTag(models.Model):
    name = models.CharField(max_length=50)
    business = models.ForeignKey('accounts.Business', related_name='client_tags', on_delete=models.CASCADE, null=True, blank=True)
    color = models.CharField(max_length=7, default='#0ea5e9')

    class Meta:
        unique_together = ('name', 'business')
        ordering = ['name']

    def __str__(self):
        return self.name


class Client(models.Model):
    STATUS_LEAD = 'LEAD'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_PAST = 'PAST'
    STATUS_INACTIVE = 'INACTIVE'
    STATUS_CHOICES = [
        (STATUS_LEAD, 'Lead'),
        (STATUS_ACTIVE, 'Active Client'),
        (STATUS_PAST, 'Past Client'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    business = models.ForeignKey('accounts.Business', related_name='clients', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=120)
    company = models.CharField(max_length=160, blank=True)
    contact_name = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_LEAD)
    source = models.CharField(max_length=120, blank=True, help_text='Where this client or lead came from.')
    notes = models.TextField(blank=True)
    tags = models.ManyToManyField(ClientTag, blank=True, related_name='clients')
    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-pinned_at', 'name']

    def __str__(self):
        return self.name


class ClientOpportunity(models.Model):
    STATUS_OPEN = 'OPEN'
    STATUS_WON = 'WON'
    STATUS_PAUSED = 'PAUSED'
    STATUS_LOST = 'LOST'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_WON, 'Won'),
        (STATUS_PAUSED, 'Paused'),
        (STATUS_LOST, 'Lost'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='opportunities')
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    estimate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.name} - {self.client.name}'
