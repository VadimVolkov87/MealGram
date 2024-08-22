"""Модуль для класса приложения Foodgram."""
from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """Класс приложения."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
