from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme


def apply_pin_state(obj, should_pin):
    obj.is_pinned = should_pin
    obj.pinned_at = timezone.now() if should_pin else None
    obj.save(update_fields=["is_pinned", "pinned_at"])


def safe_redirect_target(request, fallback):
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback
