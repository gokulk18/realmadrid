# Generated by Django 5.0.6 on 2024-08-11 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserHandle', '0025_cart_cartitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemsize',
            name='size',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]