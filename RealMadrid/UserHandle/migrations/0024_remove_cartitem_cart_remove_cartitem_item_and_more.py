# Generated by Django 5.0.6 on 2024-08-10 19:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('UserHandle', '0023_cart_cartitem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitem',
            name='cart',
        ),
        migrations.RemoveField(
            model_name='cartitem',
            name='item',
        ),
        migrations.DeleteModel(
            name='Cart',
        ),
        migrations.DeleteModel(
            name='CartItem',
        ),
    ]