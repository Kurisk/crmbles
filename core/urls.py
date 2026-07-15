from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('faq/', views.faq, name='faq'),
    path('latest-update/', views.latest_update, name='latest_update'),
]
