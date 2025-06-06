# Generated by Django 5.0.6 on 2025-03-31 04:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserHandle', '0064_alter_playervideo_player_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemVisualEmbedding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('embedding', models.BinaryField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='visual_embedding', to='UserHandle.item')),
            ],
        ),
    ]
