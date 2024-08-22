"""Модуль маршрутизаторов приложения Foodgram."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from recipes.views import (CustomUserViewSet, FavoriteRecipesViewSet,
                           IngredientViewSet, RecipesViewSet,
                           ShoppingCartViewSet,
                           SubscriptionViewSet, TagViewSet)

router = routers.DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipesViewSet, basename='recipes')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/recipes/download_shopping_cart/', ShoppingCartViewSet.as_view(
        {'get': 'get_purchase_list', },),
        name='shopping_cart_download'
    ),
    path('api/', include(router.urls)),
    path('api/recipes/<id>/favorite/', FavoriteRecipesViewSet.as_view(
        {'post': 'create', 'delete': 'destroy'},),  name='favorite'
        ),
    path(r'api/recipes/<id>/get-link/', RecipesViewSet.as_view(
        {'get': 'get_link'},),),
    path('api/recipes/<id>/shopping_cart/', ShoppingCartViewSet.as_view(
        {'post': 'create', 'delete': 'destroy'},), name='shopping_cart'
    ),
    path(r'api/users/subscriptions/', SubscriptionViewSet.as_view(
        {'get': 'list'},
    ),
         name='subscriptions'
         ),
    path('api/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/users/me/avatar/', CustomUserViewSet.as_view(
        {'put': 'me', 'delete': 'me', }), name='avatar'
    ),
    path(r'api/users/<int:id>/subscribe/', SubscriptionViewSet.as_view(
        {'post': 'create', 'delete': 'destroy', }),
        name='subscribe'
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
