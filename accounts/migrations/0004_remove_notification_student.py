# Generated by Django 5.1.6 on 2025-02-25 21:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_student_level_notification"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notification",
            name="student",
        ),
    ]
