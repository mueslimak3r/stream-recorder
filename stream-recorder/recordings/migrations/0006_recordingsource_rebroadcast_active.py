# Generated by Django 5.1.4 on 2024-12-21 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recordings', '0005_alter_recordingsource_broadcast_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recordingsource',
            name='rebroadcast_active',
            field=models.BooleanField(default=False),
        ),
    ]
