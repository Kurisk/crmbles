from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.vendor_list, name='vendor_list'),
    path('create/', views.vendor_create, name='vendor_create'),
    path('<int:vendor_id>/update/', views.vendor_update, name='vendor_update'),
    path('<int:vendor_id>/delete/', views.vendor_delete, name='vendor_delete'),
    path('<int:vendor_id>/pin/', views.vendor_pin, name='vendor_pin'),
    path('tags/create/', views.vendor_tag_create, name='vendor_tag_create'),
]
