# Generated by Django 5.0.6 on 2024-10-15 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserHandle', '0038_remove_order_apartment_remove_order_city_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='address',
            field=models.CharField(default='unknown', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='apartment',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='city',
            field=models.CharField(default='unknown', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='country',
            field=models.CharField(default='unknown', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='state',
            field=models.CharField(default='unknown', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='zipcode',
            field=models.CharField(default='unknown', max_length=20),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='UserAddress',
        ),
    ]