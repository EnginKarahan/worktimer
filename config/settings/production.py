from .base import *

DEBUG = False
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="").split(",")

# iFrame-Settings: Nextcloud-Integration
X_FRAME_OPTIONS = ""  # Deaktiviert — Django setzt keinen X-Frame-Options Header
SECURE_FRAME_DENY = False

CSRF_TRUSTED_ORIGINS = [
    "https://cloud.alhambra-gesellschaft.de",
]
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True

SECURE_SSL_REDIRECT = False  # Nginx handled
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SOCIALACCOUNT_PROVIDERS = {
    "openid_connect": {
        "APPS": [
            {
                "provider_id": "nextcloud",
                "name": "Nextcloud (Alhambra Cloud)",
                "client_id": config("OIDC_CLIENT_ID", default=""),
                "secret": config("OIDC_CLIENT_SECRET", default=""),
                "settings": {
                    "server_url": config("OIDC_SERVER_URL", default=""),
                    "token_auth_method": "client_secret_post",
                    "pkce_enabled": True,
                },
            }
        ]
    }
}
