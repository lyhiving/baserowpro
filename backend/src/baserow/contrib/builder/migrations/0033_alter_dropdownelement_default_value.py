# Generated by Django 3.2.21 on 2023-12-07 14:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0032_auto_20231205_1453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dropdownelement',
            name='default_value',
            field=models.ForeignKey(help_text="This dropdowns input's default value.", null=True, on_delete=django.db.models.deletion.SET_NULL, to='builder.dropdownelementoption'),
        ),
    ]
