"""Модуль моделией приложения Recipes."""
import random
import string

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import (EMAIL_MAX_LENGTH,
                        INGREDIENT_MEASURMENT_UNIT_MAX_LENGTH,
                        INGREDIENT_NAME_MAX_LENGTH,
                        MAX_VALIDATOR_VALUE, MIN_VALIDATOR_VALUE,
                        NAME_MAX_LENGTH, RECIPE_NAME_MAX_LENGTH,
                        TAG_MAX_LENGTH)


class FoodgramUser(AbstractUser):
    """Пользовательская модель приложения."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    email = models.EmailField('Емейл', max_length=EMAIL_MAX_LENGTH,
                              unique=True)
    first_name = models.CharField('Имя', max_length=NAME_MAX_LENGTH)
    last_name = models.CharField('Фамилия', max_length=NAME_MAX_LENGTH)
    avatar = models.ImageField(
        upload_to='avatar/images/',
        null=True,
        default=None
    )

    class Meta:
        """Внутренний класс для сортировки объектов."""

        ordering = ('last_name',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Метод возвращающий имя пользователя."""
        return self.username


class Tag(models.Model):
    """Модель Тег."""

    name = models.CharField('Название', max_length=TAG_MAX_LENGTH,
                            unique=True)
    slug = models.SlugField('Слаг тэга', max_length=TAG_MAX_LENGTH,
                            unique=True)

    class Meta:
        """Внутренний класс для сортировки объектов."""

        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """Метод возвращающий имя."""
        return self.name


class Ingredient(models.Model):
    """Модель Ингредиент."""

    name = models.CharField('Название', max_length=INGREDIENT_NAME_MAX_LENGTH,
                            unique=True)
    measurement_unit = models.CharField(
        'Единица измерения', max_length=INGREDIENT_MEASURMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        """Внутренний класс для сортировки объектов."""

        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient'),
        )

    def __str__(self):
        """Метод возвращающий имя."""
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    name = models.CharField('Название рецепта',
                            max_length=RECIPE_NAME_MAX_LENGTH)
    image = models.ImageField(
        'Фото', upload_to='recipes/images/',
    )
    text = models.TextField('Текст')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientInRecipe',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=(
            MinValueValidator(
                MIN_VALIDATOR_VALUE,
                message=(f'Введенное время не может быть меньше'
                         f'{MIN_VALIDATOR_VALUE}.')
            ),
            MaxValueValidator(
                MAX_VALIDATOR_VALUE,
                message=(f'Введенное время не может быть больше'
                         f'{MAX_VALIDATOR_VALUE}.')
            )
        )
    )
    published_at = models.DateTimeField(
        'Дата и время создания',
        auto_now_add=True
    )
    short_link = models.URLField(
        'Короткая ссылка', unique=True, editable=False)

    class Meta:
        """Внутренний класс для сортировки и связанного имени объектов."""

        ordering = ('-published_at',)
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """Метод возвращающий имя."""
        return self.name

    def save(self, **kwargs):
        """Функция генерации короткой ссылки."""
        if not self.short_link:
            self.short_link = ''.join(random.choice(
                string.ascii_letters + string.digits) for _ in range(5))
        super().save(**kwargs)


class IngredientInRecipe(models.Model):
    """Промежуточная модель ингредиентов в рецепте."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(
                MIN_VALIDATOR_VALUE,
                message=(f'Введенное количество не может быть меньше'
                         f'{MIN_VALIDATOR_VALUE}.')
            ),
            MaxValueValidator(
                MAX_VALIDATOR_VALUE,
                message=(f'Введенное количество не может быть больше'
                         f'{MAX_VALIDATOR_VALUE}.')
            )
        )
    )

    class Meta:
        """Внутренний класс для русификации объектов."""

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        default_related_name = 'ingredientinrecipe'

        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredientinrecipe'),
        )

    def __str__(self):
        """Метод возвращающий имя."""
        return f'{self.ingredient.name} + {self.ingredient.measurement_unit}'


class Subscription(models.Model):
    """Модель подписки на пользователей."""

    user = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
        related_name='owner_subscriptions'
    )
    recipe_author = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
        related_name='author_subscriptions'
    )

    class Meta:
        """Класс для порядка сортировки."""

        ordering = ('recipe_author',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe_author',),
                name='unique_subscription'),
        )

    def clean(self):
        """Метод проверки подписки."""
        if self.user == self.recipe_author:
            raise ValidationError('Вы подписываетесь на самого себя.')
        return super().save(self)

    def __str__(self):
        """Метод возвращающий имя."""
        return self.recipe_author.username


class UserRecipeModel(models.Model):
    """Абстрактная модель для избранного и корзины."""

    user = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
    )

    class Meta:
        """Класс для порядка сортировки."""

        abstract = True
        ordering = ('recipe',)

    def __str__(self):
        """Метод возвращающий имя."""
        return f'{self.recipe.name} + {self._meta.verbose_name}'


class Favorite(UserRecipeModel):
    """Модель избранных рецептов."""

    class Meta:
        """Класс для порядка сортировки."""

        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorite_recipe'

        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_user_favorite_recipe'),
        )


class ShoppingCart(UserRecipeModel):
    """Модель корзины рецептов."""

    class Meta:
        """Класс для порядка сортировки."""

        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        default_related_name = 'shopping_cart_recipe'

        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_user_shoppingcart_recipe'),
        )
