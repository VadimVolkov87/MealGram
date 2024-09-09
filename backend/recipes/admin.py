"""Модуль регистрации моделей приложения и полей в админке."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .models import (Favorite, FoodgramUser, Ingredient, Recipe,
                     Subscription, Tag)

OBJECTS_PER_PAGE = 10

UserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar', 'is_subscribed',)}),
)


class RecipeIngredientInline(admin.StackedInline):
    """Класс установки внесения ингредиентов в модель Pecipe."""

    model = Recipe.ingredients.through
    min_num = 1


@admin.register(FoodgramUser)
class UsersAdmin(UserAdmin):
    """Класс настройки отображения раздела пользователей."""

    list_display = ('id', 'username', 'email', 'first_name', 'last_name',
                    'avatar', 'is_superuser',
                    'is_staff',)
    list_editable = ('username', 'email', 'first_name', 'last_name',
                     'avatar', 'is_superuser', 'is_staff',)
    ordering = ('username',)
    list_per_page = OBJECTS_PER_PAGE
    search_fields = ('username', 'email', 'first_name',)
    list_display_links = ('id',)
    empty_value_display = 'Не задано'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Класс настройки отображения раздела тегов."""

    list_display = ('id', 'name', 'slug')
    list_editable = ('name', 'slug')
    list_display_links = ('id',)
    ordering = ('name',)
    list_per_page = OBJECTS_PER_PAGE
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    empty_value_display = 'Не задано'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Класс настройки отображения раздела ингредиентов."""

    list_display = ('id', 'name', 'measurement_unit',)
    list_editable = ('name', 'measurement_unit',)
    list_display_links = ('id',)
    ordering = ('name',)
    list_per_page = OBJECTS_PER_PAGE
    search_fields = ('name',)
    empty_value_display = 'Не задано'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Класс настройки отображения раздела рецептов."""

    list_display = ('id', 'name', 'author', 'get_ingredients',
                    'get_tags', 'get_count_is_favorited',)
    list_editable = ('name', 'author',)
    list_display_links = ('id',)
    ordering = ('name',)
    search_fields = ('name', 'author',)
    list_filter = ('author', 'tags',)
    empty_value_display = 'Не задано'
    inlines = [
        RecipeIngredientInline,

    ]

    @admin.display(description='в избранном')
    def get_count_is_favorited(self, object):
        """Метод получения числа добавлений в избранное."""
        return object.favorite_recipe.all().count()

    @admin.display(description='теги')
    def get_tags(self, object):
        """Метод получения тегов."""
        return ',\n'.join((tags.name for tags in object.tags.all()))

    @admin.display(description='ингредиенты')
    def get_ingredients(self, object):
        """Метод получения ингредиентов."""
        return ',\n'.join((
            ingredients.name for ingredients in object.ingredients.all()
        ))

    @admin.display(description='картинка')
    def get_image(self, object):
        """Метод получения картинки."""
        return mark_safe(
            f'<img src={object.image.url} width="80" height="60">'
        )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Класс настройки отображения раздела избранного."""

    list_display = ('id', 'user', 'recipe',)
    list_editable = ('user', 'recipe',)
    list_display_links = ('id',)
    ordering = ('user',)
    list_per_page = OBJECTS_PER_PAGE
    search_fields = ('user',)
    list_filter = ('user', 'recipe',)
    empty_value_display = 'Не задано'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Класс настройки отображения раздела подписок."""

    list_display = ('id', 'user', 'recipe_author',)
    list_editable = ('user', 'recipe_author',)
    list_display_links = ('id',)
    ordering = ('user',)
    list_per_page = OBJECTS_PER_PAGE
    search_fields = ('user',)
    list_filter = ('user', 'recipe_author',)
    empty_value_display = 'Не задано'
