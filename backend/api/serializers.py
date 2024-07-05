from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, IntegerField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import (ModelSerializer, SerializerMethodField,
                                        StringRelatedField)
from rest_framework.validators import UniqueTogetherValidator

from core.services import (add_ingredients, Base64ImageField,
                           check_recipe, check_subscribe)
from recipes.constants import MAX_VALUE, MIN_VALUE
from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from users.constants import MAX_LENGTH_NAME
from users.models import Subscription, User


class UserSerializer(ModelSerializer):
    """Сериализатор для модели User."""

    username = CharField(max_length=MAX_LENGTH_NAME)
    is_subscribed = SerializerMethodField(method_name='get_is_subscribed')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar')
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return check_subscribe(request, obj)


class UserAvatarSerializer(ModelSerializer):
    """Сериализатор для работы с аватаром User."""

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class IngredientSerializer(ModelSerializer):
    """ Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ('__all__',)


class IngredientPostSerializer(ModelSerializer):
    """Сериализатор для модели Ingredient (POST-запросы)."""

    id = IntegerField()
    amount = IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        error_messages={
            'min_value': f'Убедитесь, что значение больше либо'
                         f' равно {MIN_VALUE}',
            'max_value': f'Убедитесь, что значение меньше либо'
                         f' равно {MAX_VALUE}',
        }
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class TagSerializer(ModelSerializer):
    """ Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = ('__all__',)


class RecipeIngredientSerializer(ModelSerializer):
    """ Сериализатор для модели RecipeIngredient (GET-запросы)."""

    name = StringRelatedField(source='ingredient.name', read_only=True)
    measurement_unit = StringRelatedField(
        source='ingredient.measurement_unit',
        read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGetSerializer(ModelSerializer):
    """Сериализатор получения информации о рецептах."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, read_only=True,
                                             source='recipe_ingredients')
    is_favorited = SerializerMethodField(method_name='get_is_favorited',
                                         read_only=True)
    is_in_shopping_cart = SerializerMethodField(
        method_name='get_is_in_shopping_cart',
        read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_in_shopping_cart', 'is_favorited',
                  'image', 'name', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        """Проверить наличие рецепта в избранном."""
        request = self.context.get('request')
        return check_recipe(request, obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Проверить наличие рецепта в списке покупок."""
        request = self.context.get('request')
        return check_recipe(request, obj, ShoppingCart)


class RecipeShortLinkSerializer(ModelSerializer):
    """Сериализатор для создания короткой ссылки на рецепт."""

    short_link = SerializerMethodField(method_name='get_short_link',
                                       read_only=True)

    class Meta:
        model = Recipe
        fields = ('short_link',)

    def get_short_link(self, obj):
        if obj.id is not None:
            base_url = 'https://127.0.0.1:8000/recipes/'
            short_link = f'{base_url}{obj.id}/'
            return short_link
        return None


class RecipeCreateUpdateSerializer(ModelSerializer):
    """ Сериализатор для модели Recipe (POST-запросы)."""

    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = IngredientPostSerializer(many=True,
                                           source='recipe_ingredients')
    image = Base64ImageField()
    cooking_time = IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        error_messages={
            'min_value': f'Убедитесь, что значение больше либо'
                         f' равно {MIN_VALUE} минуте',
            'max_value': f'Убедитесь, что значение меньше либо'
                         f' равно {MAX_VALUE} минут',
        }
    )

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name',
                  'text', 'cooking_time')

    def validate(self, data):
        if not self.initial_data.get('ingredients'):
            raise ValidationError('Рецепт не может быть без ингредиентов.')
        if not self.initial_data.get('tags'):
            raise ValidationError('Рецепт не может быть без тега.')
        return data

    def validate_ingredients(self, ingredients):
        ingredients_list = []
        for item in ingredients:
            try:
                ingredient = Ingredient.objects.get(id=item['id'])
            except Ingredient.DoesNotExist:
                raise ValidationError('Указан несуществующий ингредиент.')

            if ingredient in ingredients_list:
                raise ValidationError('Ингредиенты должны быть уникальными.')

            ingredients_list.append(ingredient)
        return ingredients

    def validate_tags(self, tags):
        if len(set(tags)) != len(tags):
            raise ValidationError('Теги должны быть уникальными.')
        return tags

    def validate_text(self, value):
        if not value:
            raise ValidationError('Добавьте описание.')
        return value

    def validate_image(self, obj):
        if not obj:
            raise ValidationError('Добавьте изображение.')
        return obj

    def create(self, validated_data):
        request = self.context.get('request')
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        add_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        add_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeGetSerializer(instance, context=self.context).data


class RecipeShortSerializer(ModelSerializer):
    """Сериализатор краткой информации о рецепте."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(ModelSerializer):
    """ Сериализатор для модели Favorite."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже находится в избранном пользователя',
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeShortSerializer(
            instance.recipe, context={'request': request}
        ).data


class ShoppingCartSerializer(FavoriteSerializer):
    """ Сериализатор для модели ShoppingCart."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен пользователем в список покупок.',
            )
        ]


class SubscriptionSerializer(ModelSerializer):
    """ Сериализатор для модели Subscription."""

    class Meta:
        model = Subscription
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя.',
            )
        ]

    def validate(self, data):
        request = self.context.get('request')
        if request.user == data['author']:
            raise ValidationError('Нельзя подписаться на самого себя.')
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return UserSubscribeRepresentSerializer(
            instance.author, context={'request': request}).data


class UserSubscribeRepresentSerializer(UserSerializer):
    """Сериализатор получения информации о подписке."""

    recipes = SerializerMethodField(method_name='get_recipes')
    recipes_count = SerializerMethodField(method_name='get_recipes_count')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')
        read_only_fields = ('__all__',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = obj.recipes.all()[: int(recipes_limit)]
        return RecipeShortSerializer(
            recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()