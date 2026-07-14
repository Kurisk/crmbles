from django.contrib import admin

from .models import Vendor, VendorService, VendorTag


class VendorServiceInline(admin.TabularInline):
    model = VendorService
    extra = 0


@admin.register(VendorTag)
class VendorTagAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "color")
    list_filter = ("business",)
    search_fields = ("name", "business__name")


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "has_purchased", "default_expense_category", "default_industry_item", "website", "email", "updated_at")
    list_filter = ("business", "has_purchased", "tags", "default_expense_category", "default_industry_item")
    search_fields = ("name", "description", "website", "email", "notes", "business__name", "default_expense_category__name", "default_industry_item__name")
    filter_horizontal = ("tags",)
    inlines = (VendorServiceInline,)


@admin.register(VendorService)
class VendorServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "price", "created_at")
    list_filter = ("vendor",)
    search_fields = ("name", "description", "price", "notes", "vendor__name")
