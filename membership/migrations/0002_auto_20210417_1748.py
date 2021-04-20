# Generated by Django 3.1.3 on 2021-04-17 14:48

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('membership', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='registration_date',
            field=models.DateField(default=datetime.date.today, verbose_name='Registration Date'),
        ),
        migrations.AlterField(
            model_name='user',
            name='registration_upto',
            field=models.DateField(blank=True, null=True),
        ),
    ]
