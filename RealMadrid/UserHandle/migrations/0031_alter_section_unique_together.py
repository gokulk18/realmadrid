# Generated by Django 5.0.6 on 2024-09-01 09:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('UserHandle', '0030_section_stand_seat_section_stand'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='section',
            unique_together={('stand', 'name')},
        ),
    ]
