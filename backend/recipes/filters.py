"""Модуль пользовательских фильтров."""
from django.contrib.auth.models import AnonymousUser
from django_filters import MultipleChoiceFilter
from django_filters import rest_framework as filters
from django_filters.fields import MultipleChoiceField

from .models import Ingredient, Recipe


class MultipleCharField(MultipleChoiceField):
    """Класс пользовательского поля поиска."""

    def validate(self, _):
        """Метод проверки."""
        pass


class MultipleCharFilter(MultipleChoiceFilter):
    """Пользовательский класс фильтрации."""

    field_class = MultipleCharField


class RecipeFilter(filters.FilterSet):
    """Фильтр выборки рецептов по определенным полям."""

    tags = MultipleCharFilter(
        field_name='tags__slug',
        lookup_expr='icontains',
    )
    author = filters.NumberFilter(
        field_name='author__id',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart', method='filter_is_in_shopping_cart'
    )
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited', method='filter_is_favorited'
    )

    def filter_is_favorited(self, queryset, name, value):
        """Метод фильтрации избранного."""
        if isinstance(self.request.user, AnonymousUser):
            return queryset
        recipes = self.request.user.reader.all()
        id_list = []
        for recipe in recipes:
            id_list.append(recipe.recipe_id)
        return Recipe.objects.filter(id__in=id_list)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Метод фильтрации корзины покупок."""
        if isinstance(self.request.user, AnonymousUser):
            return queryset
        recipes = self.request.user.buyer.all()
        id_list = []
        for recipe in recipes:
            id_list.append(recipe.recipe_id)
        return Recipe.objects.filter(id__in=id_list)

    class Meta:
        """Класс модели и полей фильтрации."""

        model = Recipe
        fields = ('tags', 'author', 'is_in_shopping_cart', 'is_favorited',)


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
