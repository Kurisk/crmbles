from django.contrib import admin

from .models import CapitalInjection, Expense, ExpenseCategory, ExpenseLineItem, IndustryExpenseItem, Invoice, InvoiceLineItem


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 0


class ExpenseLineItemInline(admin.TabularInline):
    model = ExpenseLineItem
    extra = 0


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "color")
    list_filter = ("business",)
    search_fields = ("name", "business__name")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "client_name", "vendor", "amount", "status", "invoice_date", "due_date")
    list_filter = ("business", "status", "project", "vendor")
    search_fields = ("title", "client_name", "notes", "project__name", "vendor__name", "business__name")
    inlines = (InvoiceLineItemInline,)


@admin.register(IndustryExpenseItem)
class IndustryExpenseItemAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "business", "category", "is_active", "created_at")
    list_filter = ("business", "industry", "category", "is_active")
    search_fields = ("name", "industry", "default_notes", "business__name", "category__name")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "amount", "status", "expense_date", "category", "vendor", "industry_item")
    list_filter = ("business", "status", "category", "vendor", "industry_item")
    search_fields = ("title", "vendor_name_fallback", "notes", "vendor__name", "business__name", "industry_item__name")
    inlines = (ExpenseLineItemInline,)


@admin.register(CapitalInjection)
class CapitalInjectionAdmin(admin.ModelAdmin):
    list_display = ("source", "business", "injection_type", "amount", "injection_date", "is_repaid")
    list_filter = ("business", "injection_type", "is_repaid")
    search_fields = ("source", "notes", "business__name")
