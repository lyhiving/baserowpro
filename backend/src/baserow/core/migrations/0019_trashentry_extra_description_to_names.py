# Generated by Django 3.2.12 on 2022-05-02 16:07

from django.contrib.postgres.fields import ArrayField
from django.db import migrations
from django.db.models import F, Func, TextField
from django.db.models.expressions import Value


def forward(apps, schema_editor):
    class StringToArray(Func):
        function = "string_to_array"
        output_field = ArrayField(base_field=TextField())

    TrashEntry = apps.get_model("core", "TrashEntry")
    TrashEntry.objects.all().update(
        names=StringToArray(F("extra_description"), Value(""))
    )


def backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0018_trashentry_names"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
