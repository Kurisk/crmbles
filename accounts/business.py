from .models import Business, BusinessMembership


def businesses_for_user(user):
    if not user.is_authenticated:
        return Business.objects.none()
    if user.profile.is_manager:
        return Business.objects.filter(is_active=True)
    return Business.objects.filter(memberships__user=user, is_active=True).distinct()


def selected_business_for_request(request):
    businesses = businesses_for_user(request.user)
    business_id = request.session.get("active_business_id")
    business = businesses.filter(pk=business_id).first() if business_id else None
    if business is None:
        business = businesses.first()
        if business:
            request.session["active_business_id"] = business.pk
    return business, businesses


def membership_for(user, business):
    if not user.is_authenticated or business is None:
        return None
    if user.profile.is_manager:
        return None
    return BusinessMembership.objects.filter(user=user, business=business).first()
