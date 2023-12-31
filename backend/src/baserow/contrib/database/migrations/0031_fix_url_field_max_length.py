# Generated by Django 2.2.11 on 2021-01-25 14:54

from django.db import connection, migrations


def forward(apps, schema_editor):
    URLField = apps.get_model("database", "URLField")

    with connection.schema_editor(atomic=False) as tables_schema_editor:
        for field in URLField.objects.all():
            table_name = f"database_table_{field.table.id}"
            field_name = f"field_{field.id}"
            tables_schema_editor.execute(
                f"""ALTER TABLE {table_name} ALTER COLUMN {field_name} TYPE text"""
            )


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ("database", "0030_auto_20210526_1939"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
