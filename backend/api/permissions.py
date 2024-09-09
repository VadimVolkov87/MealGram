"""Модуль пользовательских разрешений."""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Класс пользовательского разрешения."""

    def has_object_permission(self, request, view, obj):
        """Метод проверки является ли пользователь автором."""
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user)
