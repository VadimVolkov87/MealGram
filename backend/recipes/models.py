"""Модуль моделией приложения Recipes."""
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class CustomUser(AbstractUser):
    """Пользовательская модель приложения."""

    email = models.EmailField(max_length=254, unique=True, blank=False)
    first_name = models.CharField('Имя', max_length=150, blank=False)
    last_name = models.CharField('Фамилия', max_length=150, blank=False)
    avatar = models.ImageField(
        upload_to='avatar/images/',
        null=True,
        default=None)
    is_subscribed = models.BooleanField('Подписан', default=False,)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', 'password',)

    class Meta:
        """Внутренний класс для сортировки объектов."""

        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Метод возвращающий имя пользователя."""
        return self.username


class Tag(models.Model):
    """Модель Тег."""

    name = models.CharField('Название', max_length=32, unique=True)
    slug = models.SlugField('Слаг тэга', max_length=32, unique=True)

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

    name = models.CharField('Название', max_length=128, unique=True)
    measurement_unit = models.CharField('Единица измерения', max_length=64)

    class Meta:
        """Внутренний класс для сортировки объектов."""

        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
#        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        """Метод возвращающий имя."""
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    name = models.CharField('Название рецепта', max_length=256)
    image = models.ImageField(
        'Фото', upload_to='recipes/images/', default=None
    )
    text = models.TextField('Текст')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientInRecipe',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag, through='RecipeTag',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(
                1, message='Введенное количество меньше допустимого.'
            )
        ]
    )
    published_at = models.DateTimeField(
        'Дата и время создания',
        auto_now_add=True
    )
    is_favorited = models.BooleanField(
        'избранные', default=False
    )
    is_in_shopping_cart = models.BooleanField(
        'в корзине', default=False
    )

    REQUIRED_FIELDS = ('name', 'image', 'text', 'ingredients', 'tags',
                       'cooking_time',)

    class Meta:
        """Внутренний класс для сортировки и связанного имени объектов."""

        ordering = ('published_at',)
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """Метод возвращающий имя."""
        return self.name


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
        validators=[
            MinValueValidator(
                1, message='Введенное количество не может быть меньше 1.'
            )
        ]
    )

    class Meta:
        """Внутренний класс для русификации объектов."""

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        default_related_name = 'ingredientinrecipe'


class RecipeTag(models.Model):
    """Промежуточная модель тэгов у рецепта."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт',
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, verbose_name='Тег',
    )

    class Meta:
        """Внутренний класс для русификации объектов."""

        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'
        default_related_name = 'recipetag'


class Subscription(models.Model):
    """Модель подписки на пользователей."""

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='subscriber'
    )
    subscription = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='subscriptions'
    )

    class Meta:
        """Класс для порядка сортировки."""

        ordering = ('id',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        unique_together = ('user', 'subscription')

    def clean(self):
#        cleaned_data = super().clean()
        if self.user == self.subscription:
            raise ValidationError("Вы подписываетесь на самого себя.")
        return super().save(self)


class Favorite(models.Model):
    """Модель избранных рецептов."""

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='reader'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorite_recipe'
    )

    class Meta:
        """Класс для порядка сортировки."""

        ordering = ('id',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    """Модель корзины рецептов."""

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='buyer'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_cart_recipe'
    )

    class Meta:
        """Класс для порядка сортировки."""

        ordering = ('id',)
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'

        unique_together = ('user', 'recipe')
