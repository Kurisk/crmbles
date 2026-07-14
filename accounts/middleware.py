from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse

from .models import UserProfile
from .business import membership_for, selected_business_for_request


class CRMAccessMiddleware:
    FEATURE_PREFIXES = {
        "/projects/": "projects",
        "/documents/": "documents",
        "/vendors/": "vendors",
        "/finance/": "finance",
    }

    PUBLIC_PREFIXES = (
        "/accounts/login/",
        "/accounts/logout/",
        "/accounts/setup/",
        "/static/",
        "/media/",
        "/admin/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        is_public = path.startswith(self.PUBLIC_PREFIXES)

        if not get_user_model().objects.exists() and not is_public:
            return redirect("accounts:setup")

        if not request.user.is_authenticated and not is_public:
            return redirect(f"{reverse('accounts:login')}?next={request.get_full_path()}")

        if request.user.is_authenticated:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            if request.user.is_superuser and not profile.is_manager:
                profile.grant_manager_access()
                profile.save()
            request.business, request.businesses = selected_business_for_request(request)
            membership = membership_for(request.user, request.business)

            if request.business is None and not path.startswith("/accounts/businesses/") and profile.can_access("manage_accounts"):
                return redirect("accounts:business_list")
            can_manage_accounts = profile.is_manager or (membership and membership.can_access("manage_accounts")) or (request.business is None and profile.can_access("manage_accounts"))
            if path.startswith("/accounts/users/") and not can_manage_accounts:
                messages.error(request, "You do not have permission to manage accounts.")
                return redirect("core:dashboard")

            for prefix, feature in self.FEATURE_PREFIXES.items():
                has_access = profile.is_manager or (membership and membership.can_access(feature)) or (request.business is None and profile.can_access(feature))
                if path.startswith(prefix) and not has_access:
                    messages.error(request, "You do not have permission to use that feature.")
                    return redirect("core:dashboard")
        else:
            request.business = None
            request.businesses = []

        return self.get_response(request)
