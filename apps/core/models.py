from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Holiday(TimestampedModel):
    date = models.DateField(db_index=True)
    name = models.CharField(max_length=255)
    federal_state = models.CharField(max_length=2, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["date", "federal_state"])]
        verbose_name = "Feiertag"
        verbose_name_plural = "Feiertage"

    def __str__(self):
        return f"{self.date} – {self.name}"


class AuditLog(models.Model):
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.BigIntegerField()
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["actor", "created_at"]),
        ]
        verbose_name = "Audit-Log"
        verbose_name_plural = "Audit-Logs"

    @classmethod
    def log(cls, actor, action, entity, old=None, new=None, request=None):
        ip = None
        if request:
            ip = request.META.get("REMOTE_ADDR")
        cls.objects.create(
            actor=actor,
            action=action,
            entity_type=entity.__class__.__name__,
            entity_id=entity.pk,
            old_values=old,
            new_values=new,
            ip_address=ip,
        )
