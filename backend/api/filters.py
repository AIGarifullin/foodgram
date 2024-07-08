from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """ Фильтр для модели Ingredient."""

    name = filters.CharFilter(field_name='name',
                              lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """ Фильтр для модели Recipe."""

    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             queryset=Tag.objects.all(),
                                             to_field_name='slug')
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        user_id = self.request.user.id
        if user_id and value:
            return self.queryset.filter(favorites__user_id=user_id)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user_id = self.request.user.id
        if user_id and value:
            return self.queryset.filter(shoppingcarts__user_id=user_id)
        return queryset
