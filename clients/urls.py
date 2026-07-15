from django.urls import path

from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('create/', views.client_create, name='client_create'),
    path('<int:client_id>/update/', views.client_update, name='client_update'),
    path('<int:client_id>/delete/', views.client_delete, name='client_delete'),
    path('<int:client_id>/pin/', views.client_pin, name='client_pin'),
    path('tags/create/', views.client_tag_create, name='client_tag_create'),
]
