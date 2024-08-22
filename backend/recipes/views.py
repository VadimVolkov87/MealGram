"""Модуль представлений приложения."""
from wsgiref.util import FileWrapper

from django.db.models import F, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.urls import reverse
from djoser.views import UserViewSet
from rest_framework import filters, mixins, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .models import CustomUser, Ingredient, Recipe, ShoppingCart, Tag
from .permissions import IsOwnerOnly, IsOwnerOrReadOnly
from .serializers import (CustomUserSerializer, FavoriteRecipesSerializer,
                          IngredientSerializer, RecipeGetSerializer,
                          RecipesSerializer, ShoppingCartSerializer,
                          SubscriptionSerializer, TagSerializer)


class ListCreateDestroyViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    """Класс пользовательского вьюсета."""

    pass


class ShoppingCartViewSet(ListCreateDestroyViewSet):
    """Класс представления корзины покупок."""

    permission_classes = (IsAuthenticated, IsOwnerOnly,)
    serializer_class = ShoppingCartSerializer
    lookup_field = 'id'
    http_method_names = ('get', 'post', 'delete',)

    def get_queryset(self):
        """Метод получения избранного пользователя."""
        return self.request.user.buyer.all().select_related(
            'recipe'
        ).prefetch_related('ingredientinrecipe', 'ingredient'
                           )

    def perform_create(self, serializer):
        """Метод добавления рецепта в покупки."""
        recipe = get_object_or_404(
            Recipe,
            id=self.kwargs.get('id')
        )
        serializer.save(
            user=self.request.user,
            recipe=recipe
        )

    def destroy(self, request, *args, **kwargs):
        """Метод удаления рецепта из покупок."""
        shopping_cart_recipe = request.user.buyer.filter(
            recipe_id=self.kwargs.get('id'))
        try:
            Recipe.objects.get(id=self.kwargs.get('id'))
        except Exception:
            raise NotFound(
                detail="Такого рецепта не существует.",
                code=404
            )
        if not shopping_cart_recipe.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        shopping_cart_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_purchase_list(self, request, *args, **kwargs):
        """Метод отправки файла со списком покупок."""
        purchase_list = ShoppingCart.objects.filter(
            user=request.user).order_by('recipe__ingredients__name').filter(
                recipe__ingredients__name__exact=F('recipe__ingredients__name')
        ).values(
                'recipe__ingredients__name',
                'recipe__ingredients__measurement_unit'
        ).annotate(total_amount=Sum(
            'recipe__ingredientinrecipe__amount'
        ))
        with open('shopping_list.txt', 'w') as file:
            for purchase in purchase_list:
                name = purchase["recipe__ingredients__name"]
                unit = purchase["recipe__ingredients__measurement_unit"]
                total_amount = purchase['total_amount']
                file.write(f'{name} ({unit}) - {total_amount}\n')
        file = open('shopping_list.txt', 'r')
        return HttpResponse(FileWrapper(file),
                            content_type='application/txt')


class FavoriteRecipesViewSet(ListCreateDestroyViewSet):
    """Класс представления избранного."""

    permission_classes = (IsAuthenticated, IsOwnerOnly,)
    serializer_class = FavoriteRecipesSerializer
    lookup_field = 'id'
    http_method_names = ('get', 'post', 'delete',)

    def get_queryset(self):
        """Метод получения избранного пользователя."""
        return self.request.user.reader.all()

    def perform_create(self, serializer):
        """Метод добавления рецепта в избранное."""
        recipe = get_object_or_404(
            Recipe,
            id=self.kwargs.get('id')
        )
        serializer.save(
            user=self.request.user,
            recipe=recipe
        )

    def destroy(self, request, *args, **kwargs):
        """Метод удаления рецепта из избранного."""
        favorite_recipe = request.user.reader.filter(
            recipe_id=self.kwargs.get('id'))
        try:
            Recipe.objects.get(id=self.kwargs.get('id'))
        except Exception:
            raise NotFound(
                detail="Такого рецепта не существует.",
                code=404
            )
        if not favorite_recipe.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        favorite_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet):
    """Класс представления CustomUserViewSet."""

    permission_classes = (IsAuthenticated,)
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def update(self, request):
        """Метод для обновления данных профиля пользователем."""
        user = get_object_or_404(CustomUser, id=request.user.id)
        serializer = CustomUserSerializer(
            user, data=request.data, partial=True
        )
        if serializer.is_valid() and 'avatar' in request.data:
            serializer.save()
            return Response({"avatar": serializer.data.get('avatar')},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Метод удаления аватара."""
        user_avatar = get_object_or_404(CustomUser, id=request.user.id).avatar
        user_avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    """Класс представления тэгов."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'id'
    http_method_names = ('get',)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Класс представления ингредиентов."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    lookup_field = 'id'
    http_method_names = ('get',)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class SubscriptionViewSet(ListCreateDestroyViewSet):
    """View класс для модели подписок."""

    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('get', 'post', 'delete',)
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('subscription__username',)

    def get_queryset(self):
        """Метод получения подписок пользователя."""
        return self.request.user.subscriber.all()

    def perform_create(self, serializer):
        """Метод для сохранения автора запроса."""
        subscription = get_object_or_404(
            CustomUser,
            id=self.kwargs.get('id')
        )
        serializer.save(
            user=self.request.user,
            subscription=subscription
        )

    def destroy(self, request, *args, **kwargs):
        """Метод удаления подписки."""
        subscription = request.user.subscriber.filter(
            subscription_id=self.kwargs.get('id'))
        try:
            CustomUser.objects.get(id=self.kwargs.get('id'))
        except Exception:
            raise NotFound(
                detail="Такого автора не существует.",
                code=404
            )
        if not subscription.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipesViewSet(viewsets.ModelViewSet):
    """Класс представления тэгов."""

    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    queryset = Recipe.objects.all()
    serializer_class = RecipesSerializer
    lookup_field = 'id'
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        """Метод для сохранения автора запроса."""
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Метод выбора сериализатора."""
        if self.action in ('retrieve', 'list'):
            return RecipeGetSerializer
        return RecipesSerializer

    def get_link(self, request, *args, **kwargs):
        """Метод получения ссылки на рецепт."""
        short_link = request.build_absolute_uri(reverse(
            'recipes-detail', kwargs={'id': self.kwargs.get('id')}
        ))
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)
