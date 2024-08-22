"""Модуль поьзовательского валидатора."""
import collections

from rest_framework import serializers

from .models import Ingredient


def ingredient_validator(ingredients):
    """Функция проведения проверки ингредиентов."""
    ingredient_id_list = []
    for ingredient in ingredients:
        if not Ingredient.objects.filter(id=ingredient['id']).exists():
            raise serializers.ValidationError(
                'Такого ингредиента не существует.'
            )
        if int(ingredient['amount']) < 1:
            raise serializers.ValidationError(
                'Количество ингредиента не может быть меньше 1.'
            )
        ingredient_id_list.append(ingredient['id'])
    count_ingredients = collections.Counter(ingredient_id_list)
    if 2 in count_ingredients.values():
        raise serializers.ValidationError(
                'Вы ввели повторяющиеся ингредиенты.'
            )
