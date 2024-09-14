"""Модуль представлений приложения."""
from django.shortcuts import get_object_or_404, redirect
from rest_framework.decorators import api_view

from recipes.models import Recipe


@api_view(('GET', ))
def recipe_shortlinked_retreave(request, short_link):
    """Функция возврата рецепта по короткой ссылке."""
    recipe = get_object_or_404(Recipe,
                               short_link=short_link)
    return redirect('recipes-detail', id=recipe.id)
