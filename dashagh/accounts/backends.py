from django.contrib.auth.backends import ModelBackend, BaseBackend
from .models import CustomUser
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

UserModel = get_user_model()


class SettingsBackend(ModelBackend):
    def authenticate(self, request, email=None, username=None, password=None):
        try:
            user = UserModel.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username))
            if user.check_password(password):
                return user
        except ObjectDoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            user = CustomUser.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return None

        return user if self.user_can_authenticate(user) else None
