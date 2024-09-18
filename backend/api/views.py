"""Модуль представлений приложения."""
from django.db.models import Count, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .paginators import RecipesPageNumberPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (FavoriteRecipesSerializer, FoodgramUserSerializer,
                          IngredientSerializer, RecipeGetSerializer,
                          RecipesSerializer, ShoppingCartSerializer,
                          SubscriptionPostSerializer,
                          SubscriptionGetSerializer, TagSerializer)
from recipes.models import (Favorite, FoodgramUser, Ingredient,
                            IngredientInRecipe,
                            Recipe, ShoppingCart, Tag)


class FoodgramUserViewSet(UserViewSet):
    """Класс представления CustomUserViewSet."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = FoodgramUser.objects.all()
    serializer_class = FoodgramUserSerializer
    pagination_class = RecipesPageNumberPagination

    @action(detail=False, methods=('get',), url_path='me',
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        """Метод получения своих данных пользователем."""
        serializer = FoodgramUserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=('put',), url_path='me/avatar')
    def avatar(self, request, id=None):
        """Метод загрузки аватара пользователем."""
        user = request.user
        serializer = FoodgramUserSerializer(
            user, data=request.data, context={'request': request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'avatar': serializer.data.get('avatar')},
                        status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request, id=None):
        """Метод удаления аватара."""
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post',), url_path='subscribe')
    def subscribe(self, request, id=None):
        """Метод для создания подписки."""
        subscription = get_object_or_404(
            FoodgramUser,
            id=self.kwargs.get('id')
        )
        serializer = SubscriptionPostSerializer(
            data={'user': request.user.id,
                  'recipe_author': subscription.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscription(self, request, id=None):
        """Метод для удаления подписки."""
        score, *subscription = get_object_or_404(
            FoodgramUser, id=self.kwargs.get('id')
        ).author_subscriptions.filter(user_id=request.user.id).delete()
        if not score:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',), url_path='subscriptions')
    def subscriptions(self, request):
        """Метод для вывода подписок."""
        queryset = FoodgramUser.objects.filter(
            author_subscriptions__user_id=request.user).order_by(
            'last_name').annotate(recipes_count=Count('recipes'))
        serializer = SubscriptionGetSerializer(
            self.paginate_queryset(queryset),
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Класс представления тэгов."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Класс представления ингредиентов."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    """Класс создания рецептов."""

    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'ingredients')
    lookup_field = 'id'
    pagination_class = RecipesPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Метод выбора сериализатора."""
        if self.action in ('retrieve', 'list',):
            return RecipeGetSerializer
        return RecipesSerializer

    @action(detail=True, methods=('get',), url_path='get-link')
    def get_link(self, request, *args, **kwargs):
        """Метод получения ссылки на рецепт."""
        short_link = get_object_or_404(
            Recipe, id=self.kwargs.get('id')).short_link
        return Response(
            {'short-link': request.build_absolute_uri(
                reverse('recipe_shortlinked_retreave', args=(short_link, )))},
            status=status.HTTP_200_OK
        )

    def favorite_shoppingcart_creation(self, serializer, id=None):
        """Метод создания записи избранного и корзины."""
        shopping_cart = {'user': self.request.user.id,
                         'recipe': id}
        serializer = serializer(data=shopping_cart,
                                context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def favorite_shoppingcart_deletion(self, model, id=None):
        """Метод удаления записи из корзины и избранного."""
        get_object_or_404(Recipe, id=id)
        score, *favorite_shoppingcart_object = model.objects.filter(
            user_id=self.request.user.id, recipe_id=id
        ).delete()
        if not score:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post',), url_path='shopping_cart')
    def shopping_cart(self, request, id=None):
        """Метод создания записи в корзине."""
        return self.favorite_shoppingcart_creation(
            serializer=ShoppingCartSerializer,
            id=id
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, id=None):
        """Метод удаления записи из корзины."""
        return self.favorite_shoppingcart_deletion(
            model=ShoppingCart,
            id=id
        )

    @action(detail=True, methods=('post',), url_path='favorite')
    def favorite(self, request, id=None):
        """Метод создания записи в избранном."""
        return self.favorite_shoppingcart_creation(
            serializer=FavoriteRecipesSerializer,
            id=id
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, id=None):
        """Метод удаления записи из избранного."""
        return self.favorite_shoppingcart_deletion(
            model=Favorite,
            id=id
        )

    @staticmethod
    def purchaselist_buffer_creation(purchase_list):
        """Метод загрузки строк в буфер."""
        buffer = ''
        for purchase in purchase_list:
            name = purchase['ingredient__name']
            unit = purchase['ingredient__measurement_unit']
            total_amount = purchase['total_amount']
            buffer += f'{name} ({unit}) - {total_amount},\n'
        return buffer

    @action(detail=False, methods=('get',), url_path='download_shopping_cart')
    def get_purchase_list(self, request, *args, **kwargs):
        """Метод отправки файла со списком покупок."""
        purchase_list = IngredientInRecipe.objects.filter(
            recipe__shopping_cart_recipe__user=request.user).order_by(
                'ingredient__name').values(
                'ingredient__name',
                'ingredient__measurement_unit'
        ).annotate(total_amount=Sum(
            'amount'
        ))
        return FileResponse(self.purchaselist_buffer_creation(
            purchase_list=purchase_list), as_attachment=True,
            filename='shopping_list.txt'
        )
