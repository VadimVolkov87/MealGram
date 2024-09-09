"""Модуль представлений приложения."""
from django.db.models import Count, F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .paginators import RecipesPageNumberPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (FavoriteRecipesSerializer, FoodgramUserSerializer,
                          IngredientSerializer, RecipeGetSerializer,
                          RecipesSerializer, ShoppingCartSerializer,
                          SubscriptionPostSerializer,
                          SubscriptionGetSerializer, TagSerializer)
from recipes.models import (Favorite, FoodgramUser, Ingredient, Recipe,
                            ShoppingCart, Tag)


class FoodgramUserViewSet(UserViewSet):
    """Класс представления CustomUserViewSet."""

    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly,)
    queryset = FoodgramUser.objects.all()
    serializer_class = FoodgramUserSerializer
    pagination_class = RecipesPageNumberPagination

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Метод получения своих данных пользователем."""
        if request.user.is_authenticated:
            serializer = FoodgramUserSerializer(
                get_object_or_404(FoodgramUser, id=request.user.id),
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {'detail': 'Authentication credentials were not provided.'},
            status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['put'], url_path='me/avatar')
    def avatar(self, request, id=None):
        """Метод загрузки аватара пользователем."""
        user = get_object_or_404(FoodgramUser, id=request.user.id)
        serializer = FoodgramUserSerializer(
            user, data=request.data, context={'request': request},
            partial=True,
        )
        if serializer.is_valid() and 'avatar' in request.data:
            serializer.save()
            return Response({"avatar": serializer.data.get('avatar')},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @avatar.mapping.delete
    def delete_avatar(self, request, id=None):
        """Метод удаления аватара."""
        user_avatar = get_object_or_404(
            FoodgramUser, id=request.user.id).avatar
        user_avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='subscribe')
    def subscribe(self, request, id=None):
        """Метод для создания подписки."""
        subscription = get_object_or_404(
            FoodgramUser,
            id=self.kwargs.get('id')
        )
        serializer = SubscriptionPostSerializer(
            data={'user': request.user,
                  'recipe_author': subscription},
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(
                user=request.user,
                recipe_author=subscription
            )
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    @subscribe.mapping.delete
    def delete_subscription(self, request, id=None):
        """Метод для удаления подписки."""
        subscription = request.user.owner_subscriptions.filter(
            recipe_author_id=self.kwargs.get('id'))
        try:
            FoodgramUser.objects.get(id=self.kwargs.get('id'))
        except Exception:
            raise NotFound(
                detail="Такого автора не существует.",
                code=404
            )
        if not subscription.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def subscriptions(self, request):
        """Метод для вывода подписок."""
        queryset = FoodgramUser.objects.filter(
            author_subscriptions__user_id=request.user).order_by(
            'last_name').annotate(recipes_count=Count('recipes'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            if (request.query_params != {}
               and 'limit' in request.query_params.keys()):
                n = int(request.query_params.get('limit'))
                serializer = SubscriptionGetSerializer(
                    FoodgramUser.objects.filter(
                        author_subscriptions__user_id=request.user).annotate(
                        recipes_count=Count('recipes'))[:n],
                    context={'request': request},
                    many=True)
                return self.get_paginated_response(serializer.data)
            serializer = SubscriptionGetSerializer(
                FoodgramUser.objects.filter(
                    author_subscriptions__user_id=request.user).annotate(
                    recipes_count=Count('recipes')),
                context={'request': request},
                many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionGetSerializer(
            FoodgramUser.objects.filter(
                author_subscriptions__user_id=request.user).annotate(
                recipes_count=Count('recipes')),
            context={'request': request},
            many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Класс представления тэгов."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'id'
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Класс представления ингредиентов."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    lookup_field = 'id'
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    """Класс представления тэгов."""

    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    queryset = Recipe.objects.all()
    lookup_field = 'id'
    pagination_class = RecipesPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Метод выбора сериализатора."""
        if self.action in ('retrieve', 'list'):
            return RecipeGetSerializer
        return RecipesSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, *args, **kwargs):
        """Метод получения ссылки на рецепт."""
        short_link = get_object_or_404(
            Recipe, id=self.kwargs.get('id')).short_link
        return Response(
            {'short-link': request.build_absolute_uri(f'/s/{short_link}')},
            status=status.HTTP_200_OK
        )

    def favorite_shoppingcart_creation(self, serializer, id):
        """Метод создания записи избранного и корзины."""
        shopping_cart = {'user_id': self.request.user.id,
                         'recipe_id': id}
        serializer = serializer(data=shopping_cart,
                                context={'request': self.request})
        if serializer.is_valid():
            serializer.save(
                user_id=self.request.user.id,
                recipe_id=id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def favorite_shoppingcart_deletion(self, model, id=None):
        """Метод удаления записи из корзины и избранного."""
        if not Recipe.objects.filter(id=id).exists():
            return Response({'detail': 'Not found.'},
                            status=status.HTTP_404_NOT_FOUND)
        if model.objects.filter(user_id=self.request.user.id,
                                recipe_id=id).exists():
            model.objects.filter(user_id=self.request.user.id,
                                 recipe_id=id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='shopping_cart')
    def shopping_cart(self, request, id=None):
        """Метод создания записи в корзине."""
        return self.favorite_shoppingcart_creation(
            serializer=ShoppingCartSerializer,
            id=id)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, id=None):
        """Метод удаления записи из корзины."""
        return self.favorite_shoppingcart_deletion(
            model=ShoppingCart,
            id=id
        )

    @action(detail=True, methods=['post'], url_path='favorite')
    def favorite(self, request, id=None):
        """Метод создания записи в избранном."""
        return self.favorite_shoppingcart_creation(
            serializer=FavoriteRecipesSerializer,
            id=id)

    @favorite.mapping.delete
    def delete_favorite(self, request, id=None):
        """Метод удаления записи из избранного."""
        return self.favorite_shoppingcart_deletion(
            model=Favorite,
            id=id
        )

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
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
        data = open('shopping_list.txt', 'r')
        response = HttpResponse(data, "application")
        response['Content-Disposition'
                 ] = "attachment; filename='shopping_list.txt'"
        return response


@api_view(['GET', ])
def recipe_shortlinked_retreave(request):
    """Функция возврата рецепта по короткой ссылке."""
    recipe = get_object_or_404(Recipe,
                               short_link=request.path_info.split('/')[2])
    return redirect('recipes-detail', id=recipe.id)
