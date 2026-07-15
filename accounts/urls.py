from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("setup/", views.setup_manager, name="setup"),
    path("profile/", views.profile_detail, name="profile"),
    path("password-change/", views.CRMPasswordChangeView.as_view(), name="password_change"),
    path("password-change/done/", views.CRMPasswordChangeDoneView.as_view(), name="password_change_done"),
    path("password-reset/", views.CRMPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.CRMPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", views.CRMPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", views.CRMPasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("businesses/", views.business_list, name="business_list"),
    path("businesses/create/", views.business_create, name="business_create"),
    path("businesses/<int:business_id>/update/", views.business_update, name="business_update"),
    path("businesses/<int:business_id>/pin/", views.business_pin, name="business_pin"),
    path("businesses/<int:business_id>/switch/", views.business_switch, name="business_switch"),
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:user_id>/update/", views.user_update, name="user_update"),
    path("users/<int:user_id>/deactivate/", views.user_deactivate, name="user_deactivate"),
    path("users/<int:user_id>/activate/", views.user_activate, name="user_activate"),
    path("users/<int:user_id>/delete/", views.user_delete, name="user_delete"),
]
