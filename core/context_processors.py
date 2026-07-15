from .product_info import APP_VERSION, LATEST_UPDATE, SUPPORT_EMAIL


def product_info(request):
    return {
        "app_version": APP_VERSION,
        "latest_update": LATEST_UPDATE,
        "support_email": SUPPORT_EMAIL,
    }
