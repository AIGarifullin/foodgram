from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from rest_framework import status
from rest_framework.mixins import ListModelMixin
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminAuthorOrReadOnly
from api.serializers import (IngredientSerializer, TagSerializer,
                             RecipeCreateUpdateSerializer, RecipeGetSerializer,
                             RecipeShortLinkSerializer,
                             FavoriteSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer, UserAvatarSerializer,
                             UserSubscribeRepresentSerializer)
from core.services import get_shopping_cart, RecipeFunction
from recipes.models import (Favorite, Ingredient, Recipe,
                            Tag, ShoppingCart)

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
    permission_classes = (IsAdminAuthorOrReadOnly,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAdminAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeCreateUpdateSerializer

    @action(detail=True, permission_classes=(AllowAny,),
            methods=('get',), serializer_class=RecipeShortLinkSerializer)
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        base_url = 'https://127.0.0.1:8000/recipes/'
        short_link = f'{base_url}{recipe.id}/'
        return Response({'short-link': short_link},
                        status=status.HTTP_200_OK)

    @action(detail=True, permission_classes=(IsAuthenticated,),
            methods=('post', 'delete'))
    def favorite(self, request, pk):
        """Добавление и удаление рецептов из избранного."""
        recipe_function = RecipeFunction()
        err_msg = 'Рецепт отсутствует в избранном.'
        return recipe_function.execute(
            FavoriteSerializer, Favorite, request, pk, err_msg)

    @action(detail=True, permission_classes=(IsAuthenticated,),
            methods=('post', 'delete'))
    def shopping_cart(self, request, pk):
        """Добавление и удаление рецептов из списка покупок."""
        recipe_function = RecipeFunction()
        err_msg = 'Рецепт отсутствует в списке покупок.'
        return recipe_function.execute(
            ShoppingCartSerializer, ShoppingCart, request, pk, err_msg)

    @action(detail=False, permission_classes=(IsAuthenticated,),
            methods=('get',))
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        return get_shopping_cart(request)


class SubscriptionView(APIView):
    """Подписка на пользователя."""

    permission_classes = (IsAdminAuthorOrReadOnly,)

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
