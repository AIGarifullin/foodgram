from django.contrib import admin
from django.utils.safestring import mark_safe

from recipes.constants import MIN_VALUE_AMOUNT
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Модель IngredientAdmin."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    list_display_links = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Модель TagAdmin."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')
    list_display_links = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Модель RecipeIngredientAdmin."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe', 'ingredient')
    list_filter = ('recipe', 'ingredient')


class RecipeIngredientInline(admin.TabularInline):
    """Встраиваемая форма-модель RecipeIngredientInline
    для связующей модели RecipeIngredient."""

    model = RecipeIngredient
    min_num = MIN_VALUE_AMOUNT
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Модель RecipeAdmin."""

    list_display = ('id', 'name', 'author', 'get_favorites_amount',
                    'get_ingredients', 'get_image')
    search_fields = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    list_display_links = ('name',)
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('get_favorites_amount',)

    @admin.display(description='В избранном')
    def get_favorites_amount(self, obj):
        return obj.favorites.count()

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return ', '.join([i.name for i in obj.ingredients.all()])

    @admin.display(description='Изображение')
    def get_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src={obj.image.url} '
                             'width="80" height="60">')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Модель FavoriteAdmin."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Модель ShoppingCartAdmin."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')
