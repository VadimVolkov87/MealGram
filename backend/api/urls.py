"""Модуль маршрутизаторов приложения Foodgram."""
from django.urls import include, path
from rest_framework import routers

from .views import (FoodgramUserViewSet, IngredientViewSet, RecipesViewSet,
                    TagViewSet)

router = routers.DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('users', FoodgramUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
