"""Модуль сериализаторов приложения."""
import base64

from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated

from .models import (CustomUser, Favorite, Ingredient, IngredientInRecipe,
                     Recipe, RecipeTag, ShoppingCart, Subscription, Tag)
from .validators import ingredient_validator


class Base64ImageField(serializers.ImageField):
    """Класс изображений."""

    def to_internal_value(self, data):
        """Метод преобразования изображения."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    """Класс сериализатора для пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField(
        'get_is_subscribed',
        read_only=True,
    )

    def get_is_subscribed(self, obj):
        """Метод проверки подписки пользователя."""
        if (self.instance == obj
            or isinstance(self.context['request'].user, AnonymousUser)
            or not obj.subscriptions.filter(
                 user_id=self.context['request'].user).exists()):
            return False
        return True

    def to_representation(self, instance):
        """Метод проверки пользователя на анонимность."""
        if isinstance(instance, AnonymousUser):
            raise NotAuthenticated(
                detail="Authentication credentials were not provided.",
                code=401)
        return super().to_representation(instance)

    def update(self, instance, validated_data):
        """Метод обновления записи."""
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get(
            'first_name', instance.first_name)
        instance.last_name = validated_data.get(
            'last_name', instance.last_name
        )
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance

    class Meta:
        """
        Внутренний класс сериализатора.

        Для определения модели, отображаемых и только читаемых полей.
        """

        model = CustomUser
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'avatar',)
        read_only_fields = ('id',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели тегов."""

    name = serializers.CharField(required=False)
    slug = serializers.SlugField(required=False)

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Tag
        fields = ('id', 'name', 'slug',)
        read_only_fields = ('name',)

    def __str__(self):
        """Метод возвращающий имя."""
        return self.name


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    name = serializers.CharField(required=False)
    measurement_unit = serializers.CharField(required=False)

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)
        read_only_fields = ('id',)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(required=True)

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)
        read_only_fields = ('amount',)


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения рецептов."""

    author = CustomUserSerializer(read_only=True,)
    tags = TagSerializer(many=True, read_only=True,)
    ingredients = IngredientInRecipeSerializer(
        many=True, source='ingredientinrecipe', read_only=True
    )
    image = Base64ImageField(required=True,)
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
        if isinstance(self.context['request'].user, AnonymousUser):
            return False
        if self.context['request'].user.reader.filter(
                recipe_id=obj.id).exists():
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        """Метод определения находится ли рецепт в корзине."""
        if isinstance(self.context['request'].user, AnonymousUser):
            return False
        if self.context['request'].user.buyer.filter(
                recipe_id=obj.id).exists():
            return True
        return False


class SubscriptionSerializer(serializers.ModelSerializer):
    """Класс сериализатора  модели подписок."""

    id = serializers.ReadOnlyField(source='subscription.id',)
    username = serializers.ReadOnlyField(source='subscription.username',)
    first_name = serializers.ReadOnlyField(source='subscription.first_name',)
    last_name = serializers.ReadOnlyField(source='subscription.last_name',)
    email = serializers.ReadOnlyField(source='subscription.email',)
    is_subscribed = serializers.ReadOnlyField(
        source='subscription.is_subscribed',)
    avatar = Base64ImageField(source='subscription.avatar', read_only=True)
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count')
    recipes = serializers.SerializerMethodField(
        method_name='get_recipes', read_only=True
    )

    class Meta:
        """Внутренний класс сериализатора для модели и отображаемых полей."""

        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'avatar', 'recipes_count', 'recipes',)
        model = Subscription
        read_only_fields = ('id', 'recipes_count', 'recipes',)

    def get_recipes(self, obj):
        """Метод получения рецептов."""
        if (isinstance(self.context['request'].META['QUERY_STRING'], str)
           and self.context['request'].META['QUERY_STRING'].split(
               '=')[0] == 'recipes_limit'):
            n = int(self.context['request'].META['QUERY_STRING'].split('=')[1])
            recipes_list = list(Recipe.objects.filter(
                  author_id=obj.subscription_id).values(
                  'id', 'name', 'image', 'cooking_time'))
            chunked_recipes_list = [
                   recipes_list[i:i + n]
                   for i in range(0, len(recipes_list), n)]
            if len(chunked_recipes_list) == 0:
                return list(Recipe.objects.filter(author_id=obj.subscription_id
                                                  ).values('id', 'name',
                                                           'image',
                                                           'cooking_time'))
            return [recipes_list[i:i + n] for i in range(0, len(recipes_list
                                                                ), n)][0]
        return list(Recipe.objects.filter(author_id=obj.subscription_id
                                          ).values('id', 'name', 'image',
                                                   'cooking_time'))

    def get_recipes_count(self, obj):
        """Метод расчета количества рецептов у автора."""
        return len(Recipe.objects.filter(author_id=obj.subscription_id))

    def create(self, validated_data):
        """Метод создания объекта модели."""
        return Subscription.objects.create(**validated_data)

    def validate(self, data):
        """Метод для проведения всех необходимых проверок."""
        if self.context['request'].user.subscriber.filter(
            subscription_id=self.context['request'].
                parser_context['kwargs'].get('id')
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )
        if (self.context['request'].user.id == self.context['request'].
                parser_context['kwargs'].get('id')):
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя!'
            )
        return data


class FavoriteRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор модели избранного."""

    name = serializers.ReadOnlyField(source='recipe.name')
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')
    id = serializers.ReadOnlyField(source='recipe.id')

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time',)

    def validate(self, data):
        """Метод для проведения валидации данных."""
        if self.context['request'].user.reader.filter(
            recipe_id=self.context['request'].
                parser_context['kwargs'].get('id')
        ).exists():
            raise serializers.ValidationError(
                'Вы уже добавили этот рецепт в избранное!'
            )
        return data


class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецептов."""

    author = CustomUserSerializer(read_only=True,)
    tags = TagSerializer(many=True, required=True)
    ingredients = IngredientSerializer(
        many=True, required=True)
    is_favorited = serializers.SerializerMethodField('get_is_favorited',
                                                     read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(
        'get_is_in_shopping_cart', read_only=True
    )
    image = Base64ImageField(required=True,)

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = Recipe
        fields = ('id', 'name', 'author', 'image', 'text', 'ingredients',
                  'tags', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart',)
        read_only_fields = ('id', 'author', 'is_favorited',
                            'is_in_shopping_cart',)

    def to_internal_value(self, data):
        """Метод подготовки данных тэгов для обработки."""
        new_data = data.copy()
        try:
            tags = new_data.pop('tags')
        except KeyError:
            raise serializers.ValidationError(
                {'tags': 'Тег не выбран.'})
        if data['tags'] == []:
            raise serializers.ValidationError({'tags': 'Выберите тег.'})
        repeat_tags_list = []
        tags_list = []
        for tag in tags:
            if tag in repeat_tags_list:
                raise serializers.ValidationError(
                    {'tags': 'Вы выбрали повторяющиеся теги.'})
            repeat_tags_list.append(tag)
            tag_dict = {}
            tag_dict['id'] = tag
            tags_list.append(tag_dict)
        new_data['tags'] = tags_list
        return super().to_internal_value(new_data)

    def to_representation(self, instance):
        """Метод смены сериализатора для возврата ответа."""
        return RecipeGetSerializer(
            instance=instance, context=self.context
        ).to_representation(instance)

    def get_is_favorited(self, obj):
        """Метод определения находится ли рецепт в избранном."""
        if self.context['request'].user.reader.filter(
                recipe_id=obj.id).exists():
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        """Метод определения находится ли рецепт в корзине."""
        if self.context['request'].user.buyer.filter(
                recipe_id=obj.id).exists():
            return True
        return False

    def create(self, validated_data):
        """Метод создания объекта модели."""
        if self.initial_data['ingredients'] == []:
            raise serializers.ValidationError('Требуется ввести ингредиенты.')
        validated_data.pop('tags')
        validated_data.pop('ingredients')
        tags = self.initial_data['tags']
        ingredients = self.initial_data['ingredients']
        ingredient_validator(ingredients=ingredients)
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            if not Tag.objects.filter(id=tag).exists():
                raise serializers.ValidationError(
                    'Такого тега не существует.'
                )
            current_tag = Tag.objects.get(id=tag)
            RecipeTag.objects.create(
                tag=current_tag, recipe=recipe)
        for ingredient in ingredients:
            current_ingredient_id, status = Ingredient.objects.get_or_create(
                id=ingredient['id'])
            IngredientInRecipe.objects.create(
                amount=ingredient['amount'],
                ingredient=current_ingredient_id, recipe=recipe
            )
        return recipe

    def update(self, instance, validated_data):
        """Метод обновления записи."""
        if (('ingredients' not in self.initial_data.keys())
           or (self.initial_data['ingredients'] == [])):
            raise serializers.ValidationError('Требуется ввести ингредиенты.')
        recipe = get_object_or_404(
            Recipe, id=self.context['request'].
            parser_context['kwargs'].get('id'))
        if 'tags' in validated_data.keys():
            RecipeTag.objects.filter(recipe=recipe).delete()
            validated_data.pop('tags')
            tags = self.initial_data['tags']
            for tag in tags:
                if not Tag.objects.filter(id=tag).exists():
                    raise serializers.ValidationError(
                        'Такого тега не существует.'
                    )
                current_tag = Tag.objects.get(id=tag)
                RecipeTag.objects.get_or_create(
                    tag=current_tag, recipe=recipe)
        if 'ingredients' in validated_data.keys():
            IngredientInRecipe.objects.filter(recipe=recipe).delete()
            validated_data.pop('ingredients')
            ingredients = self.initial_data['ingredients']
            ingredient_validator(ingredients=ingredients)
            for ingredient in ingredients:
                current_ingredient_id, status = (
                    Ingredient.objects.get_or_create(
                        id=ingredient['id']))
                IngredientInRecipe.objects.create(
                    amount=ingredient['amount'],
                    ingredient=current_ingredient_id, recipe=recipe
                )
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        return instance


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор модели избранного."""

    name = serializers.ReadOnlyField(source='recipe.name')
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')
    id = serializers.ReadOnlyField(source='recipe.id')

    class Meta:
        """Класс сериализатора для определения модели и отображаемых полей."""

        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time',)

    def validate(self, data):
        """Метод для проведения валидации данных."""
        if self.context['request'].user.buyer.filter(
            recipe_id=self.context['request'].
                parser_context['kwargs'].get('id')
        ).exists():
            raise serializers.ValidationError(
                'Вы уже добавили этот рецепт в корзину!'
            )
        return data
