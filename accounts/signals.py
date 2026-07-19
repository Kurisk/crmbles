from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Business, BusinessMembership, UserProfile


@receiver(pre_save, sender=get_user_model())
def normalize_username(sender, instance, **kwargs):
    if instance.username:
        instance.username = instance.username.strip().lower()


@receiver(post_save, sender=get_user_model())
def ensure_user_profile(sender, instance, created, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    if instance.is_superuser and not profile.is_manager:
        profile.grant_manager_access()
        profile.save()
    if profile.is_manager:
        for business in Business.objects.filter(is_active=True):
            membership, _ = BusinessMembership.objects.get_or_create(user=instance, business=business)
            membership.grant_full_access()
            membership.save()
