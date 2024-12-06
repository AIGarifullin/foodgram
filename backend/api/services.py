from django.db.models import Sum
from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from recipes.models import Ingredient, Recipe, RecipeIngredient


def check_recipe(request, obj, model):
    """Проверить наличия рецепта у зарегистрированного пользователя."""
    return (
        request
        and request.user.is_authenticated
        and model.objects.filter(user=request.user, recipe=obj).exists()
    )


def create_ingredients(ingredients, recipe):
    """Создать/добавить ингредиенты в рецепт."""
    ingredient_list = [
        RecipeIngredient(
            recipe=recipe,
            ingredient=Ingredient.objects.get(
                id=ingredient['ingredient']['id']),
            amount=ingredient.get('amount'),
        )
        for ingredient in ingredients
    ]
    RecipeIngredient.objects.bulk_create(ingredient_list)


def add_recipe(serializer_name, request, recipe):
    """Добавить рецепт."""
    serializer = serializer_name(
        data={'user': request.user.id, 'recipe': recipe.id},
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def delete_recipe(model, request, recipe, err_msg):
    """Удалить рецепт."""
    obj = model.objects.filter(user=request.user, recipe=recipe)
    if obj.exists():
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({'error': err_msg}, status=status.HTTP_400_BAD_REQUEST)


def execute_add_recipe(serializer_name, request, pk):
    try:
        recipe = get_object_or_404(Recipe, id=pk)
        return add_recipe(serializer_name, request, recipe)
    except Http404:
        return Response(
            {'error': 'Рецепт с указанным идентификатором не найден.'},
            status=status.HTTP_404_NOT_FOUND)


def execute_delete_recipe(model, request, pk, err_msg):
    recipe = get_object_or_404(Recipe, id=pk)
    return delete_recipe(model, request, recipe, err_msg)


def get_shopping_cart(request):
    """Получить файл со списком покупок."""
    user = request.user
    if not user.shoppingcarts.exists():
        return Response(status=status.HTTP_400_BAD_REQUEST)

    ingredients = (
        RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=request.user)
        .values(
            'ingredient__name',
            'ingredient__measurement_unit',
        )
        .annotate(ingredient_amount=Sum('amount'))
    )
    shopping_list = f'Список покупок пользователя {user}:\n'

    for ingredient in ingredients:
        name = ingredient['ingredient__name']
        unit = ingredient['ingredient__measurement_unit']
        amount = ingredient['ingredient_amount']
        shopping_list += f'\n{name} - {amount}/{unit}'

    file_name = f'{user}_shopping_cart.txt'
    response = HttpResponse(shopping_list, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={file_name}'
    return response
