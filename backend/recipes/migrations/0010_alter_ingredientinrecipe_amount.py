# Generated by Django 3.2.16 on 2024-08-14 09:04

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0009_alter_tag_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientinrecipe',
            name='amount',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Введенное количество меньше допустимого.')], verbose_name='Количество'),
        ),
    ]
