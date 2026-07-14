from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .business import businesses_for_user
from .models import Business, BusinessMembership, UserProfile


def _manager_required(view_func):
    def wrapped(request, *args, **kwargs):
        membership = None
        if getattr(request, "business", None) and not request.user.profile.is_manager:
            membership = request.user.business_memberships.filter(business=request.business).first()
        has_access = request.user.profile.is_manager or (membership and membership.can_access("manage_accounts")) or (request.business is None and request.user.profile.can_access("manage_accounts"))
        if not has_access:
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


def _apply_profile_permissions(profile, role, request):
    if role == UserProfile.ROLE_MANAGER:
        profile.grant_manager_access()
    else:
        profile.role = UserProfile.ROLE_USER
        profile.can_access_projects = _boolean_from_post(request, "can_access_projects")
        profile.can_access_documents = _boolean_from_post(request, "can_access_documents")
        profile.can_access_vendors = _boolean_from_post(request, "can_access_vendors")
        profile.can_access_finance = _boolean_from_post(request, "can_access_finance")
        profile.can_manage_accounts = _boolean_from_post(request, "can_manage_accounts")
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
            membership.can_access_finance = _boolean_from_post(request, f"business_{business.id}_finance")
            membership.can_manage_accounts = _boolean_from_post(request, f"business_{business.id}_accounts")
        membership.save()


@require_http_methods(["GET", "POST"])
def login_view(request):
    if not get_user_model().objects.exists():
        return redirect("accounts:setup")
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    form = AuthenticationForm(request, data=request.POST or None)
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
        return redirect("accounts:login")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
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
                user = User.objects.create_user(username=username, email=email, password=password1, is_staff=True)
                user.profile.grant_manager_access()
                user.profile.save()
                if not Business.objects.exists():
                    Business.objects.create(name="Dowitz Workspace", display_name="Dowitz", invoice_prefix="DOW")
                for business in Business.objects.filter(is_active=True):
                    membership, _ = BusinessMembership.objects.get_or_create(user=user, business=business)
                    membership.grant_full_access()
                    membership.save()
                login(request, user)
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
        for business in businesses:
            membership = memberships.get(business.id)
            if membership:
                encoded.append(
                    f"{business.id},{int(membership.can_access_projects)},{int(membership.can_access_documents)},"
                    f"{int(membership.can_access_vendors)},{int(membership.can_access_finance)},{int(membership.can_manage_accounts)}"
                )
        user_rows.append({"account": user, "membership_data": ";".join(encoded)})
    return render(request, "accounts/user_list.html", {"user_rows": user_rows, "roles": UserProfile.ROLE_CHOICES, "businesses": businesses})


@require_POST
@_manager_required
def user_create(request):
    User = get_user_model()
    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    role = request.POST.get("role", UserProfile.ROLE_USER)

    if not username or not password:
        messages.error(request, "Username and password are required.")
        return redirect("accounts:user_list")

    if User.objects.filter(username=username).exists():
        messages.error(request, f"Username '{username}' already exists.")
        return redirect("accounts:user_list")

    try:
        validate_password(password)
    except ValidationError as exc:
        for error in exc.messages:
            messages.error(request, error)
        return redirect("accounts:user_list")

    user = User.objects.create_user(username=username, email=email, password=password)
    user.is_staff = role == UserProfile.ROLE_MANAGER
    user.is_active = _boolean_from_post(request, "is_active")
    user.save()
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

    user.username = request.POST.get("username", user.username).strip()
    user.email = request.POST.get("email", "").strip()
    user.first_name = request.POST.get("first_name", "").strip()
    user.last_name = request.POST.get("last_name", "").strip()
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
    _apply_profile_permissions(user.profile, role, request)
    _apply_memberships(user, request)
    messages.success(request, f"Account '{user.username}' updated.")
    return redirect("accounts:user_list")


@_business_manager_required
def business_list(request):
    businesses = Business.objects.all().prefetch_related("memberships")
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
def business_switch(request, business_id):
    business = get_object_or_404(businesses_for_user(request.user), pk=business_id)
    request.session["active_business_id"] = business.pk
    messages.success(request, f"Switched to {business}.")
    return redirect(request.POST.get("next") or "core:dashboard")
