from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from recipes.constants import (MAX_ING_NAME_LENGTH, MAX_ING_MEAS_UNIT_LENGTH,
                               MAX_REC_SHORT_LINK_LENGTH, MAX_REC_NAME_LENGTH,
                               MAX_TAG_NAME_LENGTH, MAX_TAG_SLUG_LENGTH,
                               MAX_VALUE_AMOUNT, MAX_VALUE_COOKING_TIME,
                               MIN_VALUE_AMOUNT, MIN_VALUE_COOKING_TIME)
from users.models import User


class Ingredient(models.Model):
    """Модель Ingredient (Ингредиент)."""

    name = models.CharField(verbose_name='Название',
                            max_length=MAX_ING_NAME_LENGTH,
                            db_index=True,)
    measurement_unit = models.CharField(verbose_name='Единица измерения',
                                        max_length=MAX_ING_MEAS_UNIT_LENGTH)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit',
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель Tag (Тег)."""

    name = models.CharField(verbose_name='Название',
                            max_length=MAX_TAG_NAME_LENGTH,
                            unique=True)
    slug = models.SlugField(verbose_name='Слаг',
                            max_length=MAX_TAG_SLUG_LENGTH,
                            unique=True,
                            db_index=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель Recipe (Рецепт)."""

    name = models.CharField(verbose_name='Название',
                            max_length=MAX_REC_NAME_LENGTH)
    text = models.TextField(verbose_name='Описание')
    image = models.ImageField(verbose_name='Изображение',
                              upload_to='recipes/images/',
                              default='default_recipe_image.png')
    author = models.ForeignKey(User,
                               verbose_name='Автор',
                               related_name='recipes',
                               on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIngredient',
        related_name='recipes')
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                MIN_VALUE_COOKING_TIME,
                'Время приготовления должно быть'
                f' не менее {MIN_VALUE_COOKING_TIME} минут(ы).'
            ),
            MaxValueValidator(
                MAX_VALUE_COOKING_TIME,
                'Время приготовления должно быть'
                f' не более {MAX_VALUE_COOKING_TIME} минут.'
            ),
        ])
    pub_date = models.DateTimeField(verbose_name='Дата публикации',
                                    auto_now_add=True)
    short_link = models.CharField(verbose_name='Короткая ссылка',
                                  max_length=MAX_REC_SHORT_LINK_LENGTH,
                                  unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class BaseFavoriteShoppingCart(models.Model):
    """Базовая модель для моделей Favorite (Избранное)
    и ShoppingCart (Список покупок)."""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        default_related_name = '%(class)ss'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_%(class)s',
            )
        ]
        abstract = True


class Favorite(BaseFavoriteShoppingCart):
    """Модель Favorite (Избранное)."""

    class Meta(BaseFavoriteShoppingCart.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return (f'{self.user.username} добавил(а)'
                f'{self.recipe.name} в избранное.')


class ShoppingCart(BaseFavoriteShoppingCart):
    """Модель ShoppingCart (Список покупок)."""

    class Meta(BaseFavoriteShoppingCart.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        db_table = 'recipes_shopping_cart'

    def __str__(self):
        return (f'{self.user.username} добавил'
                f' {self.recipe.name} в список покупок.')


class RecipeIngredient(models.Model):
    """Связующая модель RecipeIngredient (Ингредиент рецепта)."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиентов',
        validators=[
            MinValueValidator(
                MIN_VALUE_AMOUNT,
                'Количество ингредиентов должно быть'
                f' не менее {MIN_VALUE_AMOUNT}.'
            ),
            MaxValueValidator(
                MAX_VALUE_AMOUNT,
                'Количество ингредиентов должно быть'
                f' не более {MAX_VALUE_AMOUNT}.'
            ),
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        db_table = 'recipes_recipe_ingredient'
        ordering = ('id',)

    def __str__(self):
        return self.recipe.name
