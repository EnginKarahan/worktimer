from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]
SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-insecure-key-change-me")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += ["django_extensions"]
