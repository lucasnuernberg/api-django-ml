# Generated by Django 4.1.3 on 2023-04-05 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meli', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contaml',
            name='seller_id',
            field=models.IntegerField(default=321321),
            preserve_default=False,
        ),
    ]
