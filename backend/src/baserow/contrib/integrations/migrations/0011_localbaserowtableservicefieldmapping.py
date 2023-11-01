# Generated by Django 3.2.21 on 2023-11-01 11:58

import django.db.models.deletion
import django.db.models.manager
from django.db import migrations, models

import baserow.core.formula.field


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0077_blacklistedtoken"),
        ("database", "0133_formviewfieldoptions_field_component"),
        ("integrations", "0010_localbaserowupsertrow"),
    ]

    operations = [
        migrations.CreateModel(
            name="LocalBaserowTableServiceFieldMapping",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "value",
                    baserow.core.formula.field.FormulaField(
                        default="", help_text="The field mapping's value."
                    ),
                ),
                (
                    "field",
                    models.ForeignKey(
                        help_text="The Baserow field that this mapping relates to.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="database.field",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        help_text="The LocalBaserow Service that this field mapping relates to.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="field_mappings",
                        to="core.service",
                    ),
                ),
            ],
            managers=[
                ("objects_and_trash", django.db.models.manager.Manager()),
            ],
        ),
    ]
