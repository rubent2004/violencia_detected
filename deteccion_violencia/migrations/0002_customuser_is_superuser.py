# Generated by Django 5.1 on 2024-10-26 01:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deteccion_violencia', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_superuser',
            field=models.BooleanField(default=False),
        ),
    ]
