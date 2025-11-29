from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import (
    generate_student_credentials,
    generate_lecturer_credentials,
    send_new_account_email,
)


@receiver(post_save, sender='accounts.User')
def post_save_account_receiver(sender, instance, created=False, **kwargs):
    """
    Send email notification only on account creation for active accounts
    """
    if created and instance.is_active and (instance.is_student or instance.is_lecturer):
        # Disconnect signal temporarily to avoid recursion
        post_save.disconnect(post_save_account_receiver, sender='accounts.User')

        try:
            # Generate credentials for new accounts
            if instance.is_student:
                username, password = generate_student_credentials()
            else:  # is_lecturer
                username, password = generate_lecturer_credentials()

            instance.username = username
            instance.set_password(password)
            instance.save(update_fields=['username', 'password'])

            # Send email with generated credentials
            send_new_account_email(instance, password)

        finally:
            # Reconnect signal
            post_save.connect(post_save_account_receiver, sender='accounts.User')
