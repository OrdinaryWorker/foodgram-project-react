from django.db.models import F, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.mixins import CreateAndDeleteMixin
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (FollowSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeListSerializer, RecipeMinifiedSerializer,
                             TagSerializer, UserExtendedSerializer)
from api.utils import create_shopping_list_pdf, get_data_for_shopping_list
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User


class CustomUserViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserExtendedSerializer
    permission_classes = (IsAuthenticated,)

    def get_author(self) -> User:
        return get_object_or_404(User, id=self.kwargs.get("author_id"))

    def get_object(self):
        return get_object_or_404(
            Follow, user=self.request.user, author=self.get_author()
        )

    def get_serializer_class(self):
        if self.action in ('create', 'destroy'):
            return FollowSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return User.objects.filter(following__user=self.request.user)
        return None

    def create(self, request, *args, **kwargs):
        request.data.update(author=self.get_author())
        super().create(request, *args, **kwargs)
        serializer = self.serializer_class(
            instance=self.get_author(), context=self.get_serializer_context()
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        self.get_author()
        try:
            self.get_object()
        except Http404:
            data = {
                'errors': 'На данного пользователя не была оформлена подписка.'
            }
            return JsonResponse(data, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(author=self.get_author())


class TagsViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

    http_method_names = ['get', ]


class IngredientViewSet(ModelViewSet):
    serializer_class = IngredientSerializer
    pagination_class = None
    queryset = Ingredient.objects.all()
    filter_backends = [IngredientFilter, ]
    search_fields = ['^name', ]


class RecipeViewSet(ModelViewSet, CreateAndDeleteMixin):
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in (
            'shopping_cart',
            'favorite',
            'download_shopping_cart'
        ):
            return [IsAuthenticated(), ]
        elif self.action == 'destroy':
            return [IsAuthorOrReadOnly(), ]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        elif self.action in ('shopping_cart', 'favorite'):
            return RecipeMinifiedSerializer
        return RecipeListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['post', 'get', 'delete'], detail=True)
    def favorite(self, request, pk=None):
        return self.create_and_delete_related(
            pk=pk,
            klass=Favorite,
            created_failed_message='Рецепт не добавлен в избранное',
            delete_failed_message='Рецепт отсутствует в избранном',
            field_to_create_or_delete_name='recipe'
        )

    @action(methods=['get', 'post', 'delete'], detail=True)
    def shopping_cart(self, request, pk=None):
        return self.create_and_delete_related(
            pk=pk,
            klass=ShoppingCart,
            created_failed_message='Рецепт не добавлен в список покупок',
            delete_failed_message='Рецепт отсутствует в списке покупок',
            field_to_create_or_delete_name='recipe'
        )

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        items = RecipeIngredient.objects.select_related(
            'recipe', 'ingredient'
        )

        if request.user.is_authenticated:
            items = items.filter(recipe__shopping_carts__user=request.user)
        else:
            items = items.filter(
                recipe_id__in=request.session['purchases']
            )

        items = items.values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            name=F('ingredient__name'),
            units=F('ingredient__measurement_unit'),
            total=Sum('amount'),
        ).order_by('-total')

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_list.pdf"')
        items_list = get_data_for_shopping_list(items)
        response = create_shopping_list_pdf(response, items_list)
        return response
