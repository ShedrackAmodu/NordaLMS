from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows login with either email or username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Override the authenticate method to allow login with email or username.
        """
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        try:
            # Try to fetch user by username or email (case-insensitive)
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.DoesNotExist:
            # No user found with given username/email
            return None
        else:
            # Found a user, check password
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None

    def get_user(self, user_id):
        """
        Return the user object for the given user_id.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
