# Generated by Django 5.2 on 2025-04-20 07:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_alter_organization_invite_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organization",
            name="invite_code",
            field=models.CharField(default="32a66be454", max_length=10, unique=True),
        ),
    ]
