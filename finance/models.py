from django.db import models
from django.utils import timezone

class ExpenseCategory(models.Model):
    business = models.ForeignKey('accounts.Business', related_name='expense_categories', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#6366f1')

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'business')

    def __str__(self):
        return self.name


class IndustryExpenseItem(models.Model):
    business = models.ForeignKey('accounts.Business', related_name='industry_expense_items', on_delete=models.CASCADE, null=True, blank=True)
    industry = models.CharField(max_length=120, help_text="e.g. Restaurant, Construction, Retail")
    name = models.CharField(max_length=160, help_text="e.g. Food inventory, jobsite fuel, packaging supplies")
    category = models.ForeignKey(ExpenseCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='industry_items')
    default_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['industry', 'name']
        unique_together = ('business', 'industry', 'name')

    def __str__(self):
        return f"{self.industry} - {self.name}"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]
    business = models.ForeignKey('accounts.Business', related_name='invoices', on_delete=models.CASCADE, null=True, blank=True)
    client_name = models.CharField(max_length=150)
    title = models.CharField(max_length=200, help_text="e.g. Custom Sticker Design, Consulting")
    project = models.ForeignKey('projects.Project', null=True, blank=True, on_delete=models.SET_NULL, related_name='invoices')
    vendor = models.ForeignKey('vendors.Vendor', null=True, blank=True, on_delete=models.SET_NULL, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SENT')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-invoice_date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.client_name} (${self.amount})"


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} (${self.amount})"


class Expense(models.Model):
    STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('PENDING', 'Pending'),
    ]
    business = models.ForeignKey('accounts.Business', related_name='expenses', on_delete=models.CASCADE, null=True, blank=True)
    vendor = models.ForeignKey('vendors.Vendor', null=True, blank=True, on_delete=models.SET_NULL, related_name='expenses')
    vendor_name_fallback = models.CharField(max_length=150, blank=True, help_text="Used if vendor is not in directory")
    industry_item = models.ForeignKey(IndustryExpenseItem, null=True, blank=True, on_delete=models.SET_NULL, related_name='expenses')
    title = models.CharField(max_length=200, help_text="e.g. AWS hosting, Polymailers Order")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField(default=timezone.now)
    category = models.ForeignKey(ExpenseCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='expenses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PAID')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.title} (${self.amount})"


class ExpenseLineItem(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='line_items')
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} (${self.amount})"


class CapitalInjection(models.Model):
    TYPE_CHOICES = [
        ('LOAN', 'Loan (Repayable)'),
        ('PERSONAL_OUT_OF_POCKET', 'Owner Out-of-Pocket'),
        ('EQUITY', 'Equity Contribution'),
        ('OTHER', 'Other Funding'),
    ]
    business = models.ForeignKey('accounts.Business', related_name='capital_injections', on_delete=models.CASCADE, null=True, blank=True)
    source = models.CharField(max_length=150, help_text="e.g. John Doe (Loan), Personal Account")
    injection_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='LOAN')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    injection_date = models.DateField(default=timezone.now)
    is_repaid = models.BooleanField(default=False, help_text="Checked if loan has been fully repaid")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-injection_date', '-created_at']

    def __str__(self):
        return f"{self.source} - {self.get_injection_type_display()} (${self.amount})"
