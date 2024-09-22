"""Модуль представлений приложения."""
from django.shortcuts import get_object_or_404, redirect
from rest_framework.decorators import api_view

from recipes.models import Recipe


@api_view(('GET', ))
def recipe_shortlinked_retreave(request, slug):
    """Функция возврата рецепта по короткой ссылке."""
    recipe = get_object_or_404(Recipe,
                               short_link=slug)
    return redirect(f'/recipes/{recipe.id}/')
