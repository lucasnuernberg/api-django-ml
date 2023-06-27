# Generated by Django 4.1.3 on 2023-04-07 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meli', '0002_contaml_seller_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tokenml',
            name='last_update',
        ),
        migrations.AddField(
            model_name='tokenml',
            name='access_token_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
