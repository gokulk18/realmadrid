# Generated by Django 5.0.6 on 2025-02-04 04:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserHandle', '0041_alter_quizquestion_question_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='JigsawImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='jigsaw_images/')),
                ('pieces', models.JSONField(default=list)),
            ],
        ),
    ]
