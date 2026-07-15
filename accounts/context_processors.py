def business_context(request):
    feature_access = {
        "projects": False,
        "documents": False,
        "vendors": False,
        "clients": False,
        "finance": False,
        "manage_accounts": False,
    }
    if getattr(request, "user", None) and request.user.is_authenticated:
        profile = request.user.profile
        membership = None
        business = getattr(request, "business", None)
        if business and not profile.is_manager:
            membership = request.user.business_memberships.filter(business=business).first()
        for feature in feature_access:
            if feature == "manage_accounts":
                feature_access[feature] = profile.is_manager
            else:
                feature_access[feature] = profile.is_manager or (membership and membership.can_access(feature)) or (business is None and profile.can_access(feature))
    return {
        "active_business": getattr(request, "business", None),
        "available_businesses": getattr(request, "businesses", []),
        "feature_access": feature_access,
    }
