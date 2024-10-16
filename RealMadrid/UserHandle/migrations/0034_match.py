# Generated by Django 5.0.6 on 2024-09-03 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserHandle', '0033_section_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('match_id', models.CharField(max_length=100, unique=True)),
                ('home_team', models.CharField(max_length=100)),
                ('away_team', models.CharField(max_length=100)),
                ('utc_date', models.DateTimeField()),
                ('ist_date', models.DateTimeField()),
                ('competition', models.CharField(max_length=100)),
                ('status', models.CharField(max_length=50)),
                ('venue', models.CharField(blank=True, max_length=100, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['utc_date'],
            },
        ),
    ]
