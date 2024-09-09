"""Модуль пользовательского метода."""
from recipes.models import IngredientInRecipe


def create_ingredients_list(recipe_id, ingredients):
    """Метод создания списка ингредиентов."""
    ingredients_list = []
    for ingredient in ingredients:
        new_ingredient = IngredientInRecipe(
            recipe_id=recipe_id,
            ingredient_id=ingredient['id'].id,
            amount=ingredient['amount'],
        )
        ingredients_list.append(new_ingredient)
    return ingredients_list
