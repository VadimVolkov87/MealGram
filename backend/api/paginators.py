"""Модуль пользовательской пагинации."""
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)


class CustomPageNumberPagination(PageNumberPagination):
    """Класс пользовательской пагинации."""

    page_size_query_param = 'limit'


class CustomPagination(LimitOffsetPagination):
    """Класс пагинации переопределяющий имя параметра запроса."""

    limit_query_param = 'recipes_limit'
