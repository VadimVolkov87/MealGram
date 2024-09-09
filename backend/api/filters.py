"""Модуль пользовательских фильтров."""
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтр выборки рецептов по определенным полям."""

    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        lookup_expr='icontains',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart', method='filter_is_in_shopping_cart'
    )
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited', method='filter_is_favorited'
    )

    class Meta:
        """Класс модели и полей фильтрации."""

        model = Recipe
        fields = ('tags', 'author', 'is_in_shopping_cart', 'is_favorited',)

    def filter_is_favorited(self, queryset, name, value):
        """Метод фильтрации избранного."""
        if self.request.user.is_authenticated:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Метод фильтрации корзины покупок."""
        if self.request.user.is_authenticated:
            return queryset.filter(
                shopping_cart_recipe__user=self.request.user)
        return queryset


class IngredientFilter(filters.FilterSet):
    """Класс фильтра для выбора по началу названия игредиента."""

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        """Класс модели и полей фильтрации."""

        model = Ingredient
        fields = ('name',)
