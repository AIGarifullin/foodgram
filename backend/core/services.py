import base64

from django.core.files.base import ContentFile
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from recipes.models import Ingredient, Recipe, RecipeIngredient


class Base64ImageField(serializers.ImageField):
    """Декодирование изображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


def check_recipe(request, obj, model):
    """Проверить наличия рецепта у зарегистрированного пользователя."""
    return (
        request
        and request.user.is_authenticated
        and model.objects.filter(user=request.user, recipe=obj).exists()
    )


def check_subscribe(request, author):
    """Проверить наличия подписки у зарегистрированного пользователя."""
    return (
        request.user.is_authenticated
        and request.user.follower.filter(author=author).exists()
    )


def add_ingredients(ingredients, recipe):
    """Добавить ингредиенты в рецепт."""
    ingredient_list = [
        RecipeIngredient(
            recipe=recipe,
            ingredient=Ingredient.objects.get(id=ingredient.get('id')),
            amount=ingredient.get('amount'),
        )
        for ingredient in ingredients
    ]
    RecipeIngredient.objects.bulk_create(ingredient_list)


class RecipeFunction:
    """Добавить, удалить рецепт."""

    @staticmethod
    def __add_recipe(serializer_name, request, recipe):
        """Добавить рецепт."""
        serializer = serializer_name(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def __delete_recipe(model, request, err_msg, recipe):
        """Удалить рецепт."""
        obj = model.objects.filter(user=request.user, recipe=recipe)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': err_msg}, status=status.HTTP_400_BAD_REQUEST)

    def execute(self, serializer_name, model, request, pk, err_msg):
        """Проверить тип и обработать запрос."""
        if request.method == 'POST':
            try:
                recipe = get_object_or_404(Recipe, id=pk)
            except Recipe.DoesNotExist:
                raise ValidationError(
                    'Рецепт с указанным идентификатором не существует.'
                )
            return self.__add_recipe(serializer_name, request, recipe)

        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            return self.__delete_recipe(model, request, err_msg, recipe)


def get_shopping_cart(request):
    """Получить файл со списком покупок."""
    user = request.user
    if not user.carts.exists():
        return Response(status=status.HTTP_400_BAD_REQUEST)

    ingredients = (
        RecipeIngredient.objects.filter(recipe__carts__user=request.user)
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
