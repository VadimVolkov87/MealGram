"""Модуль пользовательской пагинации."""
from rest_framework.pagination import PageNumberPagination


class RecipesPageNumberPagination(PageNumberPagination):
    """Класс пользовательской пагинации."""

    page_size_query_param = 'limit'
