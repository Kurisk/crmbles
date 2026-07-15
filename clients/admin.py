from django.contrib import admin

from .models import Client, ClientOpportunity, ClientTag


class ClientOpportunityInline(admin.TabularInline):
    model = ClientOpportunity
    extra = 0


@admin.register(ClientTag)
class ClientTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'color')
    list_filter = ('business',)
    search_fields = ('name', 'business__name')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'company', 'contact_name', 'status', 'email', 'phone', 'updated_at')
    list_filter = ('business', 'status', 'tags')
    search_fields = ('name', 'company', 'contact_name', 'email', 'phone', 'website', 'source', 'notes', 'business__name')
    filter_horizontal = ('tags',)
    inlines = (ClientOpportunityInline,)


@admin.register(ClientOpportunity)
class ClientOpportunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'status', 'estimate', 'created_at')
    list_filter = ('status', 'client')
    search_fields = ('name', 'description', 'notes', 'client__name')
