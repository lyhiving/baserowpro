# Generated by Django 2.2.2 on 2020-01-13 19:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0002_booleanfield_field_numberfield_textfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="field",
            name="primary",
            field=models.BooleanField(default=False),
        ),
    ]
