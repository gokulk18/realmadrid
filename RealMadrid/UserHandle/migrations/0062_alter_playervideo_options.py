# Generated by Django 5.0.6 on 2025-03-18 17:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('UserHandle', '0061_playervideo_status'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='playervideo',
            options={'get_latest_by': 'uploaded_at', 'ordering': ['-uploaded_at']},
        ),
    ]
