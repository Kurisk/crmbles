from django.contrib import admin

from .models import Business, BusinessMembership, UserProfile


class BusinessMembershipInline(admin.TabularInline):
    model = BusinessMembership
    extra = 0


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "team", "supervisor", "office", "phone_number", "can_manage_accounts")
    list_filter = ("role", "can_access_projects", "can_access_documents", "can_access_vendors", "can_access_clients", "can_access_finance", "can_manage_accounts")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name", "team", "office", "phone_number")


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "display_name", "city", "state", "is_active", "updated_at")
    list_filter = ("is_active", "state", "country")
    search_fields = ("name", "display_name", "legal_name", "email", "website")
    inlines = (BusinessMembershipInline,)


@admin.register(BusinessMembership)
class BusinessMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "business", "can_access_projects", "can_access_documents", "can_access_vendors", "can_access_clients", "can_access_finance", "can_manage_accounts")
    list_filter = ("business", "can_access_projects", "can_access_documents", "can_access_vendors", "can_access_clients", "can_access_finance", "can_manage_accounts")
    search_fields = ("user__username", "business__name")
