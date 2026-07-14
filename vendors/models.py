from django.db import models

class VendorTag(models.Model):
    """
    Tags used to categorize what kind of products or services a vendor offers
    (e.g., 'Apparel', 'Stickers', 'Packaging').
    """
    name = models.CharField(max_length=50)
    business = models.ForeignKey('accounts.Business', related_name='vendor_tags', on_delete=models.CASCADE, null=True, blank=True)
    color = models.CharField(max_length=7, default='#6366f1') # Hex color code

    class Meta:
        unique_together = ('name', 'business')

    def __str__(self):
        return self.name


class Vendor(models.Model):
    """
    A vendor or supplier offering services or raw materials. Includes notes
    representing research and whether we have made purchases.
    """
    business = models.ForeignKey('accounts.Business', related_name='vendors', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, help_text="Short description of what the company does at a glance.")
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    default_expense_category = models.ForeignKey('finance.ExpenseCategory', null=True, blank=True, on_delete=models.SET_NULL, related_name='default_vendors')
    default_industry_item = models.ForeignKey('finance.IndustryExpenseItem', null=True, blank=True, on_delete=models.SET_NULL, related_name='default_vendors')
    notes = models.TextField(blank=True, help_text="Research summaries and details.")
    has_purchased = models.BooleanField(default=False, help_text="Have I ever purchased from them?")
    tags = models.ManyToManyField(VendorTag, blank=True, related_name='vendors')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class VendorService(models.Model):
    """
    Structured services, items, or offerings provided by a vendor.
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.CharField(max_length=100, blank=True, help_text="e.g. $50 or $3/unit")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} - {self.vendor.name}"
