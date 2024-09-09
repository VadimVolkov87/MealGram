"""Модуль класса приложения."""
from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Класс приложения api."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
