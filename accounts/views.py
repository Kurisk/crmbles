from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import (
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods, require_POST

from core.pinning import apply_pin_state, safe_redirect_target
from .business import businesses_for_user
from .models import Business, BusinessMembership, UserProfile


PROFILE_DETAIL_FIELDS = [
    "job_title",
    "office",
    "phone_number",
    "mobile_number",
    "address_line1",
    "address_line2",
    "city",
    "state",
    "postal_code",
    "country",
    "emergency_contact_name",
    "emergency_contact_phone",
]

PHOTO_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def _manager_required(view_func):
    def wrapped(request, *args, **kwargs):
        if not request.user.profile.is_manager:
            messages.error(request, "You do not have permission to manage accounts.")
            return redirect("core:dashboard")
        return view_func(request, *args, **kwargs)

    return wrapped


def _business_manager_required(view_func):
    def wrapped(request, *args, **kwargs):
        if not request.user.profile.is_manager:
            messages.error(request, "Only managers can manage business profiles.")
            return redirect("core:dashboard")
        return view_func(request, *args, **kwargs)

    return wrapped


def _boolean_from_post(request, name):
    return name in request.POST


def _save_user_identity(user, request, save=True):
    user.email = request.POST.get("email", "").strip()
    user.first_name = request.POST.get("first_name", "").strip()
    user.last_name = request.POST.get("last_name", "").strip()
    if save:
        user.save()


def _save_profile_details(profile, request, allow_restricted=False):
    for field in PROFILE_DETAIL_FIELDS:
        setattr(profile, field, request.POST.get(field, "").strip())
    if allow_restricted:
        profile.team = request.POST.get("team", "").strip()
        supervisor_id = request.POST.get("supervisor", "")
        if supervisor_id and supervisor_id.isdigit():
            profile.supervisor = get_user_model().objects.filter(pk=int(supervisor_id)).first()
        else:
            profile.supervisor = None

    photo = request.FILES.get("photo")
    if photo:
        if photo.content_type not in PHOTO_CONTENT_TYPES:
            raise ValidationError("Profile photo must be a JPG, PNG, GIF, or WebP image.")
        if photo.size > 5 * 1024 * 1024:
            raise ValidationError("Profile photo must be 5 MB or smaller.")
        profile.photo = photo
    profile.save()


def _apply_profile_permissions(profile, role, request):
    if role == UserProfile.ROLE_MANAGER:
        profile.grant_manager_access()
    else:
        profile.role = UserProfile.ROLE_USER
        profile.can_access_projects = _boolean_from_post(request, "can_access_projects")
        profile.can_access_documents = _boolean_from_post(request, "can_access_documents")
        profile.can_access_vendors = _boolean_from_post(request, "can_access_vendors")
        profile.can_access_clients = _boolean_from_post(request, "can_access_clients")
        profile.can_access_finance = _boolean_from_post(request, "can_access_finance")
        profile.can_manage_accounts = False
    profile.save()


def _apply_memberships(user, request):
    selected_business_ids = {int(value) for value in request.POST.getlist("businesses") if value.isdigit()}
    if user.profile.is_manager:
        selected_business_ids = set(Business.objects.filter(is_active=True).values_list("id", flat=True))

    BusinessMembership.objects.filter(user=user).exclude(business_id__in=selected_business_ids).delete()
    for business in Business.objects.filter(id__in=selected_business_ids):
        membership, _ = BusinessMembership.objects.get_or_create(user=user, business=business)
        if user.profile.is_manager:
            membership.grant_full_access()
        else:
            membership.can_access_projects = _boolean_from_post(request, f"business_{business.id}_projects")
            membership.can_access_documents = _boolean_from_post(request, f"business_{business.id}_documents")
            membership.can_access_vendors = _boolean_from_post(request, f"business_{business.id}_vendors")
            membership.can_access_clients = _boolean_from_post(request, f"business_{business.id}_clients")
            membership.can_access_finance = _boolean_from_post(request, f"business_{business.id}_finance")
            membership.can_manage_accounts = False
        membership.save()


def _would_remove_last_active_manager(user):
    if not user.is_active or not user.profile.is_manager:
        return False
    return not get_user_model().objects.filter(is_active=True, profile__role=UserProfile.ROLE_MANAGER).exclude(pk=user.pk).exists()


def _normalize_username(username):
    return (username or "").strip().lower()


def _create_workspace_owner(username, email, password, business_name, request=None):
    User = get_user_model()
    username = _normalize_username(username)
    user = User.objects.create_user(username=username, email=email, password=password, is_active=True)
    try:
        if request:
            _save_user_identity(user, request)
            _save_profile_details(user.profile, request)
        user.profile.role = UserProfile.ROLE_USER
        user.profile.save()
    except ValidationError:
        user.delete()
        raise

    business = Business.objects.create(
        name=business_name,
        display_name=business_name,
        invoice_prefix=business_name[:3].upper(),
    )
    membership, _ = BusinessMembership.objects.get_or_create(user=user, business=business)
    membership.grant_full_access()
    membership.save()
    return user, business


@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        username = _normalize_username(request.POST.get("username", ""))
        email = request.POST.get("email", "").strip()
        business_name = request.POST.get("business_name", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if not username:
            messages.error(request, "Username is required.")
        elif get_user_model().objects.filter(username__iexact=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
        elif password1 != password2:
            messages.error(request, "Passwords do not match.")
        else:
            if not business_name:
                business_name = f"{username}'s Workspace"
            try:
                validate_password(password1)
            except ValidationError as exc:
                for error in exc.messages:
                    messages.error(request, error)
            else:
                try:
                    user, business = _create_workspace_owner(username, email, password1, business_name, request)
                except ValidationError as exc:
                    for error in exc.messages:
                        messages.error(request, error)
                    return render(request, "accounts/signup.html")
                login(request, user)
                request.session["active_business_id"] = business.pk
                messages.success(request, "Workspace created.")
                return redirect("core:dashboard")

    return render(request, "accounts/signup.html")


@require_http_methods(["GET", "POST"])
def login_view(request):
    if not get_user_model().objects.exists():
        return redirect("accounts:signup")
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        login_data = request.POST.copy()
        login_data["username"] = _normalize_username(login_data.get("username", ""))
        form = AuthenticationForm(request, data=login_data)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") or "core:dashboard")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@require_http_methods(["GET", "POST"])
def setup_manager(request):
    User = get_user_model()
    if User.objects.exists():
        return redirect("accounts:signup")

    if request.method == "POST":
        username = _normalize_username(request.POST.get("username", ""))
        email = request.POST.get("email", "").strip()
        business_name = request.POST.get("business_name", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if not username:
            messages.error(request, "Username is required.")
        elif password1 != password2:
            messages.error(request, "Passwords do not match.")
        else:
            try:
                validate_password(password1)
            except ValidationError as exc:
                for error in exc.messages:
                    messages.error(request, error)
            else:
                try:
                    user, business = _create_workspace_owner(username, email, password1, business_name or f"{username}'s Workspace", request)
                except ValidationError as exc:
                    for error in exc.messages:
                        messages.error(request, error)
                    return render(request, "accounts/setup.html")
                login(request, user)
                request.session["active_business_id"] = business.pk
                messages.success(request, "Manager account created.")
                return redirect("core:dashboard")

    return render(request, "accounts/setup.html")


@_manager_required
def user_list(request):
    users = get_user_model().objects.select_related("profile").order_by("username")
    businesses = Business.objects.filter(is_active=True).prefetch_related("memberships")
    user_rows = []
    for user in users:
        memberships = {membership.business_id: membership for membership in user.business_memberships.all()}
        encoded = []
        access_summary = []
        for business in businesses:
            membership = memberships.get(business.id)
            if membership:
                encoded.append(
                    f"{business.id},{int(membership.can_access_projects)},{int(membership.can_access_documents)},"
                    f"{int(membership.can_access_vendors)},{int(membership.can_access_clients)},{int(membership.can_access_finance)},"
                    f"{int(membership.can_manage_accounts)}"
                )
                permission_names = []
                if membership.can_access_projects:
                    permission_names.append("Projects")
                if membership.can_access_documents:
                    permission_names.append("Documents")
                if membership.can_access_vendors:
                    permission_names.append("Vendors")
                if membership.can_access_clients:
                    permission_names.append("Clients")
                if membership.can_access_finance:
                    permission_names.append("Finance")
                if membership.can_manage_accounts:
                    permission_names.append("Accounts")
                access_summary.append(
                    {
                        "business": business,
                        "permissions": permission_names,
                    }
                )
        user_rows.append({"account": user, "membership_data": ";".join(encoded), "access_summary": access_summary})
    return render(
        request,
        "accounts/user_list.html",
        {"user_rows": user_rows, "roles": UserProfile.ROLE_CHOICES, "businesses": businesses, "supervisor_options": users},
    )


@require_POST
@_manager_required
def user_create(request):
    User = get_user_model()
    username = _normalize_username(request.POST.get("username", ""))
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    role = request.POST.get("role", UserProfile.ROLE_USER)

    if not username or not password:
        messages.error(request, "Username and password are required.")
        return redirect("accounts:user_list")

    if User.objects.filter(username__iexact=username).exists():
        messages.error(request, f"Username '{username}' already exists.")
        return redirect("accounts:user_list")

    try:
        validate_password(password)
    except ValidationError as exc:
        for error in exc.messages:
            messages.error(request, error)
        return redirect("accounts:user_list")

    user = User.objects.create_user(username=username, email=email, password=password)
    _save_user_identity(user, request, save=False)
    user.is_staff = role == UserProfile.ROLE_MANAGER
    user.is_active = _boolean_from_post(request, "is_active")
    user.save()
    try:
        _save_profile_details(user.profile, request, allow_restricted=True)
    except ValidationError as exc:
        user.delete()
        for error in exc.messages:
            messages.error(request, error)
        return redirect("accounts:user_list")
    _apply_profile_permissions(user.profile, role, request)
    _apply_memberships(user, request)
    messages.success(request, f"Account '{username}' created.")
    return redirect("accounts:user_list")


@require_POST
@_manager_required
def user_update(request, user_id):
    user = get_object_or_404(get_user_model().objects.select_related("profile"), pk=user_id)
    role = request.POST.get("role", UserProfile.ROLE_USER)

    if user == request.user and role != UserProfile.ROLE_MANAGER:
        messages.error(request, "You cannot remove your own manager role.")
        return redirect("accounts:user_list")

    username = _normalize_username(request.POST.get("username", user.username))
    if not username:
        messages.error(request, "Username is required.")
        return redirect("accounts:user_list")
    if get_user_model().objects.filter(username__iexact=username).exclude(pk=user.pk).exists():
        messages.error(request, f"Username '{username}' already exists.")
        return redirect("accounts:user_list")
    user.username = username
    _save_user_identity(user, request, save=False)
    user.is_active = _boolean_from_post(request, "is_active") or user == request.user
    user.is_staff = role == UserProfile.ROLE_MANAGER

    password = request.POST.get("password", "")
    if password:
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            for error in exc.messages:
                messages.error(request, error)
            return redirect("accounts:user_list")
        user.set_password(password)

    user.save()
    try:
        _save_profile_details(user.profile, request, allow_restricted=True)
    except ValidationError as exc:
        for error in exc.messages:
            messages.error(request, error)
        return redirect("accounts:user_list")
    _apply_profile_permissions(user.profile, role, request)
    _apply_memberships(user, request)
    messages.success(request, f"Account '{user.username}' updated.")
    return redirect("accounts:user_list")


@require_POST
@_manager_required
def user_deactivate(request, user_id):
    user = get_object_or_404(get_user_model().objects.select_related("profile"), pk=user_id)
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("accounts:user_list")
    if _would_remove_last_active_manager(user):
        messages.error(request, "You cannot deactivate the last active manager account.")
        return redirect("accounts:user_list")

    user.is_active = False
    user.save(update_fields=["is_active"])
    messages.success(request, f"Account '{user.username}' deactivated. Their login is disabled, but their account record remains available.")
    return redirect("accounts:user_list")


@require_POST
@_manager_required
def user_activate(request, user_id):
    user = get_object_or_404(get_user_model(), pk=user_id)
    user.is_active = True
    user.save(update_fields=["is_active"])
    messages.success(request, f"Account '{user.username}' reactivated.")
    return redirect("accounts:user_list")


@require_POST
@_manager_required
def user_delete(request, user_id):
    user = get_object_or_404(get_user_model().objects.select_related("profile"), pk=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("accounts:user_list")
    if _would_remove_last_active_manager(user):
        messages.error(request, "You cannot delete the last active manager account.")
        return redirect("accounts:user_list")

    username = user.username
    user.delete()
    messages.success(request, f"Account '{username}' deleted.")
    return redirect("accounts:user_list")


@_business_manager_required
def business_list(request):
    businesses = Business.objects.all().prefetch_related("memberships").order_by("-is_pinned", "-pinned_at", "name")
    return render(request, "accounts/business_list.html", {"businesses": businesses})


def _save_business_from_request(business, request):
    fields = [
        "name",
        "display_name",
        "legal_name",
        "address_line1",
        "address_line2",
        "city",
        "state",
        "postal_code",
        "country",
        "phone",
        "email",
        "website",
        "tax_id",
        "default_currency",
        "invoice_prefix",
        "brand_color",
    ]
    for field in fields:
        setattr(business, field, request.POST.get(field, "").strip())
    try:
        fiscal_month = int(request.POST.get("fiscal_year_start_month") or 1)
    except ValueError:
        fiscal_month = 1
    business.fiscal_year_start_month = max(1, min(12, fiscal_month))
    business.is_active = _boolean_from_post(request, "is_active")
    business.save()
    membership, _ = BusinessMembership.objects.get_or_create(user=request.user, business=business)
    membership.grant_full_access()
    membership.save()


@require_POST
@_business_manager_required
def business_create(request):
    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Business name is required.")
        return redirect("accounts:business_list")
    business = Business()
    _save_business_from_request(business, request)
    request.session["active_business_id"] = business.pk
    messages.success(request, f"Business '{business}' created.")
    return redirect("accounts:business_list")


@require_POST
@_business_manager_required
def business_update(request, business_id):
    business = get_object_or_404(Business, pk=business_id)
    _save_business_from_request(business, request)
    messages.success(request, f"Business '{business}' updated.")
    return redirect("accounts:business_list")


@require_POST
@_business_manager_required
def business_pin(request, business_id):
    business = get_object_or_404(Business, pk=business_id)
    apply_pin_state(business, request.POST.get("pin") == "1")
    return redirect(safe_redirect_target(request, reverse("accounts:business_list")))


@require_POST
def business_switch(request, business_id):
    business = get_object_or_404(businesses_for_user(request.user), pk=business_id)
    request.session["active_business_id"] = business.pk
    messages.success(request, f"Switched to {business}.")
    return redirect(request.POST.get("next") or "core:dashboard")


@login_required
@require_http_methods(["GET", "POST"])
def profile_detail(request):
    if request.method == "POST":
        _save_user_identity(request.user, request)
        try:
            _save_profile_details(request.user.profile, request)
        except ValidationError as exc:
            for error in exc.messages:
                messages.error(request, error)
        else:
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    return render(request, "accounts/profile.html")


class CRMPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class CRMPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class CRMPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class CRMPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class CRMPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")


class CRMPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"
