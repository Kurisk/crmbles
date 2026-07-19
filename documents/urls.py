from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('<int:pk>/', views.document_detail, name='document_detail'),
    path('create/', views.document_create, name='document_create'),
    path('<int:pk>/update/', views.document_update, name='document_update'),
    path('<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('<int:pk>/pin/', views.document_pin, name='document_pin'),
    path('<int:pk>/toggle-checklist/', views.document_checklist_toggle, name='document_checklist_toggle'),
    path('attachments/upload/', views.attachment_upload, name='attachment_upload'),
    path('attachments/<int:attachment_id>/delete/', views.attachment_delete, name='attachment_delete'),
]
