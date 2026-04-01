from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import TimestampedModel

User = get_user_model()


class Project(TimestampedModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField(blank=True)
    client = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    manager = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Projekt"
        verbose_name_plural = "Projekte"
        ordering = ["name"]

    def __str__(self):
        return self.name
