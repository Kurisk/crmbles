from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("setup/", views.setup_manager, name="setup"),
    path("businesses/", views.business_list, name="business_list"),
    path("businesses/create/", views.business_create, name="business_create"),
    path("businesses/<int:business_id>/update/", views.business_update, name="business_update"),
    path("businesses/<int:business_id>/switch/", views.business_switch, name="business_switch"),
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:user_id>/update/", views.user_update, name="user_update"),
]
