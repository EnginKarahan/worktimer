from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile, WorkSchedule
from django.utils import timezone

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)
        WorkSchedule.objects.create(
            user=instance,
            effective_from=timezone.now().date(),
        )
        from apps.overtime.models import OvertimeAccount
        OvertimeAccount.objects.get_or_create(user=instance)
