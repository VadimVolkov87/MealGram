"""Модуль сериализаторов приложения."""
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .static import create_ingredients_list
from recipes.models import (Favorite, FoodgramUser, Ingredient,
                            IngredientInRecipe, Recipe,
                            ShoppingCart, Subscription, Tag)


class FoodgramUserSerializer(UserSerializer):
    """Класс сериализатора для пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField(
        'get_is_subscribed',
        read_only=True,
    )

    class Meta(UserSerializer.Meta):
        """
        Внутренний класс сериализатора.

        Для определения модели, отображаемых и только читаемых полей.
        """

        model = FoodgramUser
        fields = ['id', 'username', 'first_name', 'last_name',
                  'email', ] + ['is_subscribed', 'avatar', ]
        read_only_fields = ['id', ]

    def get_is_subscribed(self, obj):
        """Метод проверки подписки пользователя."""
        if (self.context.setdefault(
            'request').user.is_authenticated
            and obj.author_subscriptions.filter(
                user_id=self.context.setdefault('request').user).exists()):
            return True
        return False


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели тегов."""

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Tag
        fields = ('id', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)
        read_only_fields = ('amount',)


class RecipeGetShortSerializer(serializers.ModelSerializer):
    """Сериализатор для получения коротких рецептов подписок."""

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = ('id', 'name', 'image', 'cooking_time',)


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения рецептов."""

    author = FoodgramUserSerializer(read_only=True,)
    tags = TagSerializer(many=True, read_only=True,)
    ingredients = IngredientInRecipeSerializer(
        many=True, source='ingredientinrecipe', read_only=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(
        'get_is_favorited', read_only=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        'get_is_in_shopping_cart', read_only=True
    )

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time',)
        read_only_fields = ('id', 'author', 'tags', 'is_favorited',
                            'is_in_shopping_cart',)

    def get_is_favorited(self, obj):
        """Метод определения находится ли рецепт в избранном."""
        if not self.context.setdefault('request').user.is_authenticated:
            return False
        if self.context.setdefault('request').user.favorite_recipe.filter(
                recipe_id=obj.id).exists():
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        """Метод определения находится ли рецепт в корзине."""
        if not self.context.setdefault('request').user.is_authenticated:
            return False
        if self.context.setdefault('request').user.shopping_cart_recipe.filter(
                recipe_id=obj.id).exists():
            return True
        return False


class SubscriptionGetSerializer(FoodgramUserSerializer):
    """Класс сериализатора  модели подписок."""

    recipes_count = serializers.IntegerField(default=0,)
    recipes = serializers.SerializerMethodField(
        method_name='get_recipes', read_only=True
    )

    class Meta(FoodgramUserSerializer.Meta):
        """Внутренний класс сериализатора для модели и отображаемых полей."""

        fields = ['id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'avatar', ] + ['recipes_count', 'recipes', ]

        model = FoodgramUser
        read_only_fields = ['id', ] + ['recipes_count', 'recipes', ]

    def get_recipes(self, obj):
        """Метод получения рецептов."""
        recipes_list = obj.recipes.all()
        if (self.context['request'].query_params != {}
           and 'recipes_limit' in self.context['request'].query_params.keys()):
            n = int(self.context['request'].query_params.get(
                'recipes_limit'))
            return RecipeGetShortSerializer(
                instance=recipes_list[:n], context=self.context,
                many=True
            ).data
        return RecipeGetShortSerializer(
                instance=recipes_list, context=self.context,
                many=True
        ).data


class SubscriptionPostSerializer(serializers.ModelSerializer):
    """Класс сериализатора  модели подписок."""

    class Meta:
        """Внутренний класс сериализатора для модели и отображаемых полей."""

        fields = ('user', 'recipe_author',)
        model = Subscription
        read_only_fields = ('user', 'recipe_author',)

    def validate(self, data):
        """Метод для проведения всех необходимых проверок."""
        if self.context['request'].user.owner_subscriptions.filter(
            recipe_author_id=self.context['request'].
                parser_context['kwargs'].get('id')
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )
        if (self.context['request'].user.id == int(
            self.context['request'].parser_context['kwargs'].get('id')
        )):
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя!'
            )
        return data

    def to_representation(self, instance):
        """Метод смены сериализатора для возврата ответа."""
        return SubscriptionGetSerializer(
            instance=FoodgramUser.objects.get(id=instance.recipe_author_id),
            context=self.context
        ).to_representation(FoodgramUser.objects.get(
            id=instance.recipe_author_id))


class FavoriteShoppingcartBaseSerializer(serializers.ModelSerializer):
    """Сериализатор модели избранного."""

    name = serializers.ReadOnlyField(source='recipe.name')
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')
    id = serializers.ReadOnlyField(source='recipe.id')

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        fields = ('id', 'name', 'image', 'cooking_time',)

    def validate(self, data):
        """Метод для проведения валидации данных."""
        if not get_object_or_404(Recipe, id=self.context.get('request').
                                 parser_context['kwargs'].get('id')):
            raise serializers.ValidationError(
                'Такого рецепта не существует!',
                code=404
            )
        if self.Meta.model.objects.filter(
            recipe_id=self.context.get('request').
            parser_context['kwargs'].get('id'),
            user_id=self.context.get('request').user.id
        ).exists():
            raise serializers.ValidationError(
                'Вы уже добавили этот рецепт!'
            )
        return data


class FavoriteRecipesSerializer(FavoriteShoppingcartBaseSerializer):
    """Сериализатор модели избранного."""

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time',)


class IngredientInRecipeShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор модели."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),)
    amount = serializers.IntegerField()

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = IngredientInRecipe
        fields = ('id', 'amount',)

    def validate_amount(self, value):
        """Метод валидации количества."""
        if value < 1:
            raise serializers.ValidationError(
                'Введенное количество не может быть меньше 1.')
        return value


class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецептов."""

    author = FoodgramUserSerializer(read_only=True,)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True, required=True, allow_empty=False)
    ingredients = IngredientInRecipeShortSerializer(
        many=True, required=True, allow_empty=False)
    image = Base64ImageField(
        required=True, allow_null=False, allow_empty_file=False)

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Recipe
        fields = ('id', 'name', 'author', 'image', 'text', 'ingredients',
                  'tags', 'cooking_time',)
        read_only_fields = ('id', 'author',)

    def validate_image(self, value):
        """Метод валидации картинки."""
        if value is None:
            raise serializers.ValidationError('Выберите картинку.')
        return value

    def validate_tags(self, value):
        """Метод валидации тегов."""
        repeat_tags_list = []
        for tag in value:
            if tag in repeat_tags_list:
                raise serializers.ValidationError(
                    {'tags': 'Вы выбрали повторяющиеся теги.'})
            repeat_tags_list.append(tag)
        return value

    def validate_ingredients(self, value):
        """Метод валидации ингредиентов."""
        repeat_ingredients_list = []
        for ingredient in value:
            if ingredient in repeat_ingredients_list:
                raise serializers.ValidationError(
                    {'ingredients': 'Вы выбрали повторяющиеся ингредиенты.'})
            repeat_ingredients_list.append(ingredient)
        return value

    def validate(self, data):
        """Метод для проведения всех необходимых проверок."""
        if 'ingredients' not in data.keys():
            raise serializers.ValidationError('Требуется ввести ингредиенты.')
        if 'tags' not in data.keys():
            raise serializers.ValidationError('Требуется выбрать тег.')
        return data

    def to_representation(self, instance):
        """Метод смены сериализатора для возврата ответа."""
        return RecipeGetSerializer(
            instance=instance, context=self.context
        ).to_representation(instance)

    def create(self, validated_data):
        """Метод создания объекта модели."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        ingredients_list = create_ingredients_list(
            recipe_id=recipe.id, ingredients=ingredients
        )
        IngredientInRecipe.objects.bulk_create(ingredients_list)
        return recipe

    def update(self, instance, validated_data):
        """Метод обновления записи."""
        recipe = get_object_or_404(
            Recipe, id=self.context['request'].
            parser_context['kwargs'].get('id'))
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe.tags.set(tags)
        IngredientInRecipe.objects.filter(recipe=recipe).delete()
        ingredients_list = create_ingredients_list(
            recipe_id=recipe.id, ingredients=ingredients
        )
        IngredientInRecipe.objects.bulk_create(ingredients_list)
        return super().update(instance=instance, validated_data=validated_data)


class ShoppingCartSerializer(FavoriteShoppingcartBaseSerializer):
    """Сериализатор модели избранного."""

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time',)
