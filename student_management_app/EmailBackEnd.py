from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackEnd(ModelBackend):
    def authenticate(self,username=None, password=None, **kwargs):
        UserModel=get_user_model()
        if not username:
            return None
        user = UserModel.objects.filter(email__iexact=username).order_by("id").first()
        if user and user.check_password(password):
            return user
        return None
