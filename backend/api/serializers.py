"""Модуль сериализаторов приложения."""
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import MAX_VALIDATOR_VALUE, MIN_VALIDATOR_VALUE
from recipes.models import (Favorite, FoodgramUser, Ingredient,
                            IngredientInRecipe, Recipe,
                            ShoppingCart, Subscription, Tag)


class FoodgramUserSerializer(UserSerializer):
    """Класс сериализатора для пользователя."""

    avatar = Base64ImageField()
    is_subscribed = serializers.SerializerMethodField(
        read_only=True,
    )

    class Meta(UserSerializer.Meta):
        """
        Внутренний класс сериализатора.

        Для определения модели, отображаемых и только читаемых полей.
        """

        model = FoodgramUser
        fields = UserSerializer.Meta.fields + ('is_subscribed', 'avatar', )

    def get_is_subscribed(self, obj):
        """Метод проверки подписки пользователя."""
        request = self.context.get('request')
        return (request.user.is_authenticated
                and obj.author_subscriptions.filter(
                    user_id=request.user).exists())

    def validate(self, data):
        """Метод валидации количества."""
        if data == {}:  # Пустая строка не ловится без этого метода.
            raise serializers.ValidationError(
                'Поле аватара не может быть пустым.',
                code=400
            )
        return data


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
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

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
        request = self.context.get('request')
        return (request.user.is_authenticated
                and request.user.favorite_recipe.filter(
                    recipe_id=obj.id
                ).exists())

    def get_is_in_shopping_cart(self, obj):
        """Метод определения находится ли рецепт в корзине."""
        request = self.context.get('request')
        return (request.user.is_authenticated
                and request.user.shopping_cart_recipe.filter(
                    recipe_id=obj.id).exists())


class SubscriptionGetSerializer(FoodgramUserSerializer):
    """Класс сериализатора  модели подписок."""

    recipes_count = serializers.IntegerField(default=0,)
    recipes = serializers.SerializerMethodField(read_only=True)

    class Meta(FoodgramUserSerializer.Meta):
        """Внутренний класс сериализатора для модели и отображаемых полей."""

        model = FoodgramUser
        fields = FoodgramUserSerializer.Meta.fields + (
            'recipes_count', 'recipes',
        )
        read_only_fields = ('id', 'recipes_count', 'recipes', )

    def get_recipes(self, obj):
        """Метод получения рецептов."""
        recipes_list = obj.recipes.all()
        try:
            recipes_limit = int(self.context['request'].query_params.get(
                'recipes_limit'
            ))
        except (ValueError, TypeError):
            recipes_limit = None
        instance = recipes_list[:recipes_limit]
        return RecipeGetShortSerializer(
            instance=instance, context=self.context,
            many=True
        ).data


class SubscriptionPostSerializer(serializers.ModelSerializer):
    """Класс сериализатора  модели подписок."""

    class Meta:
        """Внутренний класс сериализатора для модели и отображаемых полей."""

        fields = ('user', 'recipe_author',)
        model = Subscription

    def validate(self, data):
        """Метод для проведения всех необходимых проверок."""
        user = data.get('user')
        recipe_author = data.get('recipe_author')
        if user.owner_subscriptions.filter(recipe_author_id=recipe_author.id
                                           ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )
        if user == recipe_author:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя!'
            )
        return data

    def to_representation(self, instance):
        """Метод смены сериализатора для возврата ответа."""
        return SubscriptionGetSerializer(instance=instance.recipe_author,
                                         context=self.context).data


class FavoriteShoppingcartBaseSerializer(serializers.ModelSerializer):
    """Сериализатор модели избранного."""

    def validate(self, data):
        """Метод для проведения валидации данных."""
        if self.Meta.model.objects.filter(
            recipe_id=data.get('recipe').id,
            user_id=data.get('user').id
        ).exists():
            raise serializers.ValidationError(
                'Вы уже добавили этот рецепт!'
            )
        return data

    def to_representation(self, instance):
        """Метод смены сериализатора для возврата ответа."""
        return RecipeGetShortSerializer(instance=instance.recipe,
                                        context=self.context).data


class FavoriteRecipesSerializer(FavoriteShoppingcartBaseSerializer):
    """Сериализатор модели избранного."""

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Favorite
        fields = ('user', 'recipe',)


class IngredientInRecipeShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор модели."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),)
    amount = serializers.IntegerField(min_value=MIN_VALIDATOR_VALUE,
                                      max_value=MAX_VALIDATOR_VALUE)

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = IngredientInRecipe
        fields = ('id', 'amount',)


class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецептов."""

    author = FoodgramUserSerializer(read_only=True,)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True, required=True, allow_empty=False
    )
    ingredients = IngredientInRecipeShortSerializer(
        many=True, required=True, allow_empty=False,
    )
    image = Base64ImageField(required=True,
                             allow_empty_file=False, allow_null=False)

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Recipe
        fields = ('id', 'name', 'author', 'image', 'text', 'ingredients',
                  'tags', 'cooking_time',)
        read_only_fields = ('id', 'author',)

    def validate_image(self, value):
        """Метод валидации картинки."""
        if not value:
            raise serializers.ValidationError('Выберите картинку.')
        return value

    def validate_tags(self, value):
        """Метод валидации тегов."""
        if list(set(value)) != value:
            raise serializers.ValidationError(
                {'tags': 'Вы выбрали повторяющиеся теги.'}
            )
        return value

    def validate_ingredients(self, value):
        """Метод валидации ингредиентов."""
        ingredients_list = [ingredient.get('id') for ingredient in value]
        if len(set(ingredients_list)) != len(ingredients_list):
            raise serializers.ValidationError(
                {'ingredients': 'Вы выбрали повторяющиеся ингредиенты.'}
            )
        return value

    def validate(self, data):
        """Метод для проверки наличия поля."""
        if 'ingredients' not in data.keys():
            raise serializers.ValidationError('Требуется ввести ингредиенты.')
        if 'tags' not in data.keys():
            raise serializers.ValidationError('Требуется выбрать тег.')
        return data

    def to_representation(self, instance):
        """Метод смены сериализатора для возврата ответа."""
        return RecipeGetSerializer(
            instance=instance, context=self.context
        ).data

    @staticmethod
    def create_ingredients(recipe_id, ingredients):
        """Метод создания списка ингредиентов."""
        ingredients_list = []
        for ingredient in ingredients:
            new_ingredient = IngredientInRecipe(
                recipe_id=recipe_id,
                ingredient_id=ingredient['id'].id,
                amount=ingredient['amount'],
            )
            ingredients_list.append(new_ingredient)
        return IngredientInRecipe.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        """Метод создания объекта модели."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(
            recipe_id=recipe.id, ingredients=ingredients
        )
        return recipe

    def update(self, instance, validated_data):
        """Метод обновления записи."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.set(tags)
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(
            recipe_id=instance.id, ingredients=ingredients
        )
        return super().update(instance=instance, validated_data=validated_data)


class ShoppingCartSerializer(FavoriteShoppingcartBaseSerializer):
    """Сериализатор модели избранного."""

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = ShoppingCart
        fields = ('user', 'recipe',)
