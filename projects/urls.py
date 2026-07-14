from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('create/', views.project_create, name='project_create'),
    path('<int:project_id>/lists/create/', views.task_list_create, name='task_list_create'),
    path('lists/<int:list_id>/tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/toggle/', views.task_toggle, name='task_toggle'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:task_id>/update/', views.task_update, name='task_update'),
    path('tasks/<int:task_id>/notes/create/', views.task_note_create, name='task_note_create'),
    path('<int:project_id>/tasks/quick-add/', views.task_quick_add, name='task_quick_add'),
    path('lists/<int:list_id>/update/', views.task_list_update, name='task_list_update'),
    path('lists/<int:list_id>/delete/', views.task_list_delete, name='task_list_delete'),
    path('<int:project_id>/tags/create/', views.tag_create, name='tag_create'),
]
