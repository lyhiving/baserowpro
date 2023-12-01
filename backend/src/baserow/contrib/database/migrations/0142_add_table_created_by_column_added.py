# Generated by Django 3.2.21 on 2023-12-01 13:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0141_formview_users_to_notify_on_submit"),
    ]

    operations = [
        migrations.CreateModel(
            name="CreatedByField",
            fields=[
                (
                    "field_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="database.field",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("database.field",),
        ),
        migrations.AddField(
            model_name="table",
            name="created_by_column_added",
            field=models.BooleanField(
                default=False,
                null=True,
                help_text="Indicates whether the table has had the created_by column added.",
            ),
            preserve_default=False,
        ),
    ]
