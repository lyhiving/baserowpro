# Generated by Django 2.2.11 on 2020-07-01 16:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0007_datefield"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datefield",
            name="date_format",
            field=models.CharField(
                choices=[
                    ("EU", "European (D/M/Y)"),
                    ("US", "US (M/D/Y)"),
                    ("ISO", "ISO (Y-M-D)"),
                ],
                default="EU",
                help_text="EU (20/02/2020), US (02/20/2020) or ISO (2020-02-20)",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="datefield",
            name="date_include_time",
            field=models.BooleanField(
                default=False, help_text="Indicates if the field also includes a time."
            ),
        ),
        migrations.AlterField(
            model_name="datefield",
            name="date_time_format",
            field=models.CharField(
                choices=[("24", "24 hour"), ("12", "12 hour")],
                default="24",
                help_text="24 (14:30) or 12 (02:30 PM)",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="field",
            name="order",
            field=models.PositiveIntegerField(help_text="Lowest first."),
        ),
        migrations.AlterField(
            model_name="field",
            name="primary",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Indicates if the field is a primary field. If `true` the field "
                    "cannot be deleted and the value should represent the whole row."
                ),
            ),
        ),
        migrations.AlterField(
            model_name="numberfield",
            name="number_decimal_places",
            field=models.IntegerField(
                choices=[
                    (1, "1.0"),
                    (2, "1.00"),
                    (3, "1.000"),
                    (4, "1.0000"),
                    (5, "1.00000"),
                ],
                default=1,
                help_text="The amount of digits allowed after the point.",
            ),
        ),
        migrations.AlterField(
            model_name="numberfield",
            name="number_negative",
            field=models.BooleanField(
                default=False, help_text="Indicates if negative values are allowed."
            ),
        ),
        migrations.AlterField(
            model_name="textfield",
            name="text_default",
            field=models.CharField(
                blank=True,
                help_text=(
                    "If set, this value is going to be added every time a new row "
                    "created."
                ),
                max_length=255,
                null=True,
            ),
        ),
    ]
