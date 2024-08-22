# Generated by Django 3.2.16 on 2024-08-17 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0016_shoppingcart'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='is_favorited',
            field=models.BooleanField(default=False, verbose_name='избранные'),
        ),
        migrations.AddField(
            model_name='recipe',
            name='is_in_shopping_cart',
            field=models.BooleanField(default=False, verbose_name='в корзине'),
        ),
    ]
