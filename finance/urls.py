from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_dashboard, name='dashboard'),
    path('category/create/', views.category_create, name='category_create'),
    path('industry-items/create/', views.industry_item_create, name='industry_item_create'),
    path('industry-items/<int:pk>/update/', views.industry_item_update, name='industry_item_update'),
    path('industry-items/<int:pk>/delete/', views.industry_item_delete, name='industry_item_delete'),
    
    path('invoice/create/', views.invoice_create, name='invoice_create'),
    path('invoice/<int:pk>/update/', views.invoice_update, name='invoice_update'),
    path('invoice/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    
    path('expense/create/', views.expense_create, name='expense_create'),
    path('expense/<int:pk>/update/', views.expense_update, name='expense_update'),
    path('expense/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    
    path('injection/create/', views.injection_create, name='injection_create'),
    path('injection/<int:pk>/update/', views.injection_update, name='injection_update'),
    path('injection/<int:pk>/delete/', views.injection_delete, name='injection_delete'),
]
