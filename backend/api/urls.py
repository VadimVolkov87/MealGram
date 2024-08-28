"""Модуль маршрутизаторов приложения Foodgram."""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

from .views import (CustomUserViewSet, FavoriteRecipesViewSet,
                    IngredientViewSet, RecipesViewSet,
                    ShoppingCartViewSet,
                    SubscriptionViewSet, TagViewSet)

router = routers.DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipesViewSet, basename='recipes')

urlpatterns = [
    path('recipes/download_shopping_cart/', ShoppingCartViewSet.as_view(
        {'get': 'get_purchase_list', },),
        name='shopping_cart_download'
    ),
    path('', include(router.urls)),
    path('recipes/<id>/favorite/', FavoriteRecipesViewSet.as_view(
        {'post': 'create', 'delete': 'destroy'},), name='favorite'
    ),
    path(r'recipes/<id>/get-link/', RecipesViewSet.as_view(
        {'get': 'get_link'},),),
    path('recipes/<id>/shopping_cart/', ShoppingCartViewSet.as_view(
        {'post': 'create', 'delete': 'destroy'},), name='shopping_cart'
    ),
    path(r'users/subscriptions/', SubscriptionViewSet.as_view(
        {'get': 'list'},), name='subscriptions'
    ),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/avatar/', CustomUserViewSet.as_view(
        {'put': 'me', 'delete': 'me', }), name='avatar'
    ),
    path(r'users/<int:id>/subscribe/', SubscriptionViewSet.as_view(
        {'post': 'create', 'delete': 'destroy', }),
        name='subscribe'
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
