# Generated by Django 5.0.6 on 2024-08-06 16:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserHandle', '0009_item'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='image',
        ),
        migrations.AddField(
            model_name='item',
            name='main_image',
            field=models.ImageField(blank=True, null=True, upload_to='items/main/'),
        ),
        migrations.CreateModel(
            name='ItemImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='items/additional/')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='additional_images', to='UserHandle.item')),
            ],
        ),
    ]