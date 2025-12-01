#!/usr/bin/env python
"""
Test script to verify email sending functionality
"""
import os
import sys
from pathlib import Path

# Add the config directory to the Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Test email sending"""
    try:
        print("Testing email sending...")
        print(f"Email Backend: {settings.EMAIL_BACKEND}")
        print(f"Email Host: {settings.EMAIL_HOST}")
        print(f"Email Port: {settings.EMAIL_PORT}")
        print(f"Email Host User: {settings.EMAIL_HOST_USER}")
        print(f"Email From Address: {settings.EMAIL_FROM_ADDRESS}")

        # Send a test email
        subject = "Test Email from NordaLMS"
        message = "This is a test email to verify email functionality."
        recipient_list = [settings.EMAIL_HOST_USER]  # Send to same account for testing

        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_FROM_ADDRESS,
            recipient_list=recipient_list,
            fail_silently=False,
        )

        print(f"Email sent successfully! Result: {result}")
        return True

    except Exception as e:
        print(f"Email failed: {e}")
        return False

if __name__ == "__main__":
    success = test_email()
    if success:
        print("✓ Email sending works!")
    else:
        print("✗ Email sending failed. Check SMTP settings.")
