# Generated by Django 3.2.21 on 2023-10-30 11:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0077_blacklistedtoken"),
        ("database", "0133_formviewfieldoptions_field_component"),
        ("integrations", "0009_local_baserow_table_service_managers"),
    ]

    operations = [
        migrations.CreateModel(
            name="LocalBaserowUpsertRow",
            fields=[
                (
                    "service_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="core.service",
                    ),
                ),
                (
                    "filter_type",
                    models.CharField(
                        choices=[("AND", "And"), ("OR", "Or")],
                        default="AND",
                        help_text="Indicates whether all the rows should apply to all filters (AND) or to any filter (OR).",
                        max_length=3,
                    ),
                ),
                (
                    "table",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="database.table",
                    ),
                ),
                (
                    "view",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="database.view",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("core.service",),
        ),
    ]
