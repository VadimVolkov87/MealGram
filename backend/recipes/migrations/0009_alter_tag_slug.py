# Generated by Django 3.2.16 on 2024-08-10 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_auto_20240809_1648'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(default=0, max_length=32, unique=True, verbose_name='Слаг тэга'),
            preserve_default=False,
        ),
    ]
