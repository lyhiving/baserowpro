# Generated by Django 3.2.21 on 2023-10-11 14:04

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0130_alter_view_created_by"),
    ]

    operations = [
        migrations.RenameField(
            model_name="view",
            old_name="created_by",
            new_name="owned_by",
        ),
    ]
