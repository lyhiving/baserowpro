# Generated by Django 3.2.18 on 2023-06-15 09:55

from django.db import migrations

import baserow.core.fields


class Migration(migrations.Migration):
    dependencies = [
        ("baserow_premium", "0008_calendar_view"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rowcomment",
            name="updated_on",
            field=baserow.core.fields.SyncedDateTimeField(auto_now=True),
        ),
    ]
