from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_MANAGER = "MANAGER"
    ROLE_USER = "USER"
    ROLE_CHOICES = [
        (ROLE_MANAGER, "Manager"),
        (ROLE_USER, "User"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    can_access_projects = models.BooleanField(default=False)
    can_access_documents = models.BooleanField(default=False)
    can_access_vendors = models.BooleanField(default=False)
    can_access_finance = models.BooleanField(default=False)
    can_manage_accounts = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} profile"

    @property
    def is_manager(self):
        return self.role == self.ROLE_MANAGER or self.user.is_superuser

    def can_access(self, feature):
        if self.is_manager:
            return True
        if feature == "manage_accounts":
            return self.can_manage_accounts
        return bool(getattr(self, f"can_access_{feature}", False))

    def grant_manager_access(self):
        self.role = self.ROLE_MANAGER
        self.can_access_projects = True
        self.can_access_documents = True
        self.can_access_vendors = True
        self.can_access_finance = True
        self.can_manage_accounts = True


class Business(models.Model):
    name = models.CharField(max_length=160)
    display_name = models.CharField(max_length=160, blank=True)
    legal_name = models.CharField(max_length=200, blank=True)
    address_line1 = models.CharField(max_length=160, blank=True)
    address_line2 = models.CharField(max_length=160, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="United States")
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    tax_id = models.CharField(max_length=80, blank=True)
    default_currency = models.CharField(max_length=3, default="USD")
    fiscal_year_start_month = models.PositiveSmallIntegerField(default=1)
    invoice_prefix = models.CharField(max_length=20, blank=True)
    brand_color = models.CharField(max_length=7, default="#6366f1")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.display_name or self.name


class BusinessMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="business_memberships")
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="memberships")
    can_access_projects = models.BooleanField(default=False)
    can_access_documents = models.BooleanField(default=False)
    can_access_vendors = models.BooleanField(default=False)
    can_access_finance = models.BooleanField(default=False)
    can_manage_accounts = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "business")
        ordering = ["business__name", "user__username"]

    def __str__(self):
        return f"{self.user.username} - {self.business}"

    def can_access(self, feature):
        if feature == "manage_accounts":
            return self.can_manage_accounts
        return bool(getattr(self, f"can_access_{feature}", False))

    def grant_full_access(self):
        self.can_access_projects = True
        self.can_access_documents = True
        self.can_access_vendors = True
        self.can_access_finance = True
        self.can_manage_accounts = True
