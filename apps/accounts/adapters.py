from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

User = get_user_model()


class OIDCAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """Auto-provisioning: verbindet bestehende E-Mail-Adressen automatisch."""
        if sociallogin.is_existing:
            return
        email = sociallogin.account.extra_data.get("email", "")
        if not email:
            return
        try:
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        extra = sociallogin.account.extra_data
        if not user.first_name and extra.get("given_name"):
            user.first_name = extra["given_name"]
        if not user.last_name and extra.get("family_name"):
            user.last_name = extra["family_name"]
        return user
