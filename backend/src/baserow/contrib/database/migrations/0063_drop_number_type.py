# Generated by Django 3.2.6 on 2022-02-14 13:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0062_migrate_number_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='numberfield',
            name='number_type',
        ),
    ]
