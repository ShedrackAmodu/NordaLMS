# Generated by Django 5.1.6 on 2025-02-25 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newsandevents",
            name="summary",
            field=models.TextField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name="newsandevents",
            name="summary_en",
            field=models.TextField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name="newsandevents",
            name="summary_es",
            field=models.TextField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name="newsandevents",
            name="summary_fr",
            field=models.TextField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name="newsandevents",
            name="summary_ru",
            field=models.TextField(blank=True, max_length=1000, null=True),
        ),
    ]
