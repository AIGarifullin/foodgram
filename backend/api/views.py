from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthenticatedAuthorOrReadOnly
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer, RecipeGetSerializer,
                             RecipeShortLinkSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer, TagSerializer,
                             UserAvatarSerializer,
                             UserSubscribeRepresentSerializer)
from api.services import (execute_add_recipe, execute_delete_recipe,
                          get_shopping_cart)
from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag)
from users.models import User


class UserViewSet(djoser_views.UserViewSet):
    """Вьюсет для модели User."""

    @action(detail=False, permission_classes=(IsAuthenticated,),
            methods=('get',))
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, permission_classes=(IsAuthenticated,),
            methods=('put', 'delete'), url_path='me/avatar',
            serializer_class=UserAvatarSerializer)
    def user_avatar(self, request):
        user = self.request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            user.avatar.delete()
            user.save()
            return Response(
                'Аватар удален.', status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class IngredientViewSet(ModelViewSet):
    """Вьюсет для модели Ingredient."""

    http_method_names = ['get']
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(ModelViewSet):
    """Вьюсет для модели Tag."""

    http_method_names = ['get']
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedAuthorOrReadOnly,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeCreateUpdateSerializer

    @action(detail=True, permission_classes=(AllowAny,),
            methods=('get',), serializer_class=RecipeShortLinkSerializer)
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        base_url = 'https://127.0.0.1:7000/recipes/'
        short_link = f'{base_url}{recipe.id}/'
        return Response({'short-link': short_link},
                        status=status.HTTP_200_OK)

    @action(detail=True, permission_classes=(IsAuthenticated,),
            methods=('post',))
    def favorite(self, request, pk):
        """Добавление рецептов в избранного."""
        return execute_add_recipe(FavoriteSerializer, request, pk)

    @favorite.mapping.delete
    def delete_recipe_favorite(self, request, pk):
        """Удаление рецептов из избранного."""
        err_msg = 'Рецепт отсутствует в избранном.'
        return execute_delete_recipe(Favorite, request, pk, err_msg)

    @action(detail=True, permission_classes=(IsAuthenticated,),
            methods=('post',))
    def shopping_cart(self, request, pk):
        """Добавление рецептов в список покупок."""
        return execute_add_recipe(ShoppingCartSerializer, request, pk)

    @shopping_cart.mapping.delete
    def delete_recipe_shopping_cart(self, request, pk):
        """Удаление рецептов из списка покупок."""
        err_msg = 'Рецепт отсутствует в списке покупок.'
        return execute_delete_recipe(ShoppingCart, request, pk, err_msg)

    @action(detail=False, permission_classes=(IsAuthenticated,),
            methods=('get',))
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        return get_shopping_cart(request)


class SubscriptionView(APIView):
    """Подписка на пользователя."""

    permission_classes = (IsAuthenticatedAuthorOrReadOnly,)

    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        follower = request.user.follower.filter(author=author)
        if not follower:
            return Response(
                {'error': 'Нет подписки на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST)
        follower.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscriptionsViewSet(ListModelMixin, GenericViewSet):
    """Получение списка всех подписок на пользователей."""

    serializer_class = UserSubscribeRepresentSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)
