import pdfkit
from datetime import datetime
from os import path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from django.conf import settings
from django.db.models import F, Q, Sum
from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework.response import Response
from rest_framework import status, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from api.mixins import CreateAndDeleteMixin
from api.permissioms import IsAuthorOrReadOnly
from api.serializers import (
    UserExtendedSerializer,
    TagSerializer,
    RecipeListSerializer,
    RecipeCreateUpdateSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    FollowSerializer
)
from recipes.models import (
    Tag,
    Recipe,
    RecipeIngredient,
    Ingredient,
    ShoppingCart,
    Favorite
)

from users.models import (
    User,
    Follow
)


# class CustomUserViewSet(UserViewSet, CreateAndDeleteMixin):
#     http_method_names = ['post', 'delete', 'get']
#
#     def get_permissions(self):
#         if self.action in ('subscribe', 'subscriptions'):
#             return [IsAuthenticated()]
#         else:
#             return super().get_permissions()
#
#     def get_serializer_class(self):
#         if self.action in ('create', 'destroy'):
#             return UserExtendedSerializer
#         else:
#             return super().get_serializer_class()
#
#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         if (self.action in ('subscribe', 'subscriptions')
#                 and self.request.method == 'GET'):
#             recipes_limit = self.request.query_params.get(
#                 'recipes_limit', settings.DEFAULT_RECIPES_LIMIT
#             )
#             try:
#                 context['recipes_limit'] = int(recipes_limit)
#             except ValueError:
#                 raise ValidationError(
#                     {'errors': 'recipes_limit должен быть числом'}
#                 )
#         return context
#
#     def destroy(self, request, *args, **kwargs):
#         return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
#
#     @action(methods=['post', 'delete'], detail=True)
#     def subscribe(self, request, id=None):
#         return self.create_and_delete_related(
#             pk=id,
#             klass=Follow,
#             created_failed_message='Не удалось подписаться',
#             delete_failed_message='Подписка не существует',
#             field_to_create_or_delete_name='author'
#         )
#
#     @action(methods=['get'], detail=False)
#     def subscriptions(self, request):
#         queryset = User.objects.filter(following__user=self.request.user).all()
#         # queryset = User.objects.filter(subscribed_by__user=self.request.user).all()
#         context = self.get_serializer_context()
#         page = self.paginate_queryset(queryset)
#         serializer = self.get_serializer_class()(
#             page,
#             context=context,
#             many=True
#         )
#         return self.get_paginated_response(serializer.data)

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

    def destroy(self, request, *args, **kwargs):
        self.get_author()
        try:
            self.get_object()
        except Http404:
            data = {"errors": "Нельзя отпистаться от того, на кого не подписан."}
            return JsonResponse(data, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in (
            "create",
            "destroy",
        ):
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

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get("name")
        if name is not None:
            qs_starts = queryset.filter(name__istartswith=name)
            qs_contains = queryset.filter(
                ~Q(name__istartswith=name) & Q(name__icontains=name)
            )
            queryset = list(qs_starts) + list(qs_contains)
        return queryset


class RecipeViewSet(ModelViewSet, CreateAndDeleteMixin):
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        if self.action in (
            'shopping_cart',
            'favorite',
            'download_shopping_cart'
        ):
            return [IsAuthenticated(), ]
        elif self.action == 'destroy':
            return [IsAuthorOrReadOnly(), ]
        else:
            return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        elif self.action in ('shopping_cart', 'favorite'):
            return RecipeMinifiedSerializer
        else:
            return RecipeListSerializer

    def get_queryset(self):
        tags = self.request.query_params.getlist('tags')
        user = self.request.user
        qs = Recipe.objects
        if tags:
            qs = qs.filter_by_tags(tags)
        qs = qs.add_user_annotation(user.pk)
        if self.request.query_params.get('is_favorited'):
            qs = qs.filter(is_favorited=True)
        if self.request.query_params.get('is_in_shopping_cart'):
            qs = qs.filter(is_in_shopping_cart=True)
            # qs = qs.filter(is_in_shopping_cart=True)
        author = self.request.query_params.get('author', None)
        if author:
            qs = qs.filter(author=author)
        return qs

    @action(methods=['post', 'delete'], detail=True) # get??
    def shopping_cart(self, request, pk=None):
        return self.create_and_delete_related(
            pk=pk,
            klass=ShoppingCart,
            created_failed_message='Не удалось добавить рецепт в список покупок',
            delete_failed_message='Рецепт отсутствует в списке покупок',
            field_to_create_or_delete_name='recipe'
        )

    @action(methods=['post', 'get', 'delete'], detail=True)
    def favorite(self, request, pk=None):
        return self.create_and_delete_related(
            pk=pk,
            klass=Favorite,
            created_failed_message='Не удалось добавить рецепт в избранное',
            delete_failed_message='Рецепт отсутствует в избранном',
            field_to_create_or_delete_name='recipe'
        )

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        items = RecipeIngredient.objects.select_related(
            'recipe', 'ingredient'
        )

        if request.user.is_authenticated:
            items = items.filter(recipe__shopping_carts__user=request.user) # внимание тут
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

        # text = '\n'.join([
        #     f"{item['name']} {item['units']} {item['total']}"
        #     for item in items
        # ])
        # filename = 'foodgram_shopping_cart.txt'
        # response = HttpResponse(text, content_type='text/plain')
        # response['Content-Disposition'] = f'attachment; filename={filename}'
        #
        # return response
        final_list = {}
        for item in items:
            name = item['name']
            if name not in final_list:
                final_list[name] = {
                    'measurement_unit': item['ingredient__measurement_unit'],
                    'amount': item['total']
                }
        app_path = path.realpath(path.dirname(__file__))
        font_path = path.join(app_path, 'Slimamif.ttf')
        pdfmetrics.registerFont(TTFont('Slimamif', font_path))
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_list.pdf"')
        page = canvas.Canvas(response)
        page.setFont('Slimamif', size=24)
        page.drawString(200, 800, 'Список ингредиентов')
        page.setFont('Slimamif', size=16)
        height = 750
        for i, (name, data) in enumerate(final_list.items(), 1):
            page.drawString(75, height, (f'<{i}> {name} - {data["amount"]}, '
                                         f'{data["measurement_unit"]}'))
            height -= 25
        page.showPage()
        page.save()
        return response


    # @staticmethod
    # def generate_shopping_cart_pdf(queryset, user):
    #     data = {
    #         "page_objects": queryset,
    #         "user": user,
    #         "created": datetime.now(),
    #     }
    #
    #     template = get_template("shopping_cart.html")
    #     html = template.render(data)
    #     pdf = pdfkit.from_string(html, False, options={"encoding": "UTF-8"})
    #
    #     filename = "shopping_cart.pdf"
    #     response = HttpResponse(pdf, content_type="application/pdf")
    #     response["Content-Disposition"] = f'attachment; filename="{filename}"'
    #     return response
    #
    # @action(permission_classes=((IsAuthenticated,)), detail=False)
    # def download_shopping_cart(self, request):
    #     items = RecipeIngredient.objects.select_related(
    #         'recipe', 'ingredient'
    #     )
    #     if request.user.is_authenticated:
    #         items = items.filter(recipe__shopping_carts__user=request.user.id,) # внимание тут
    #     else:
    #         items = items.filter(
    #             recipe_id__in=request.session['purchases']
    #         )
    #         items = items.value(
    #             'ingredient__name', 'ingredient__measurement_unit'
    #         ).annotate(
    #             name=F('ingredient__name'),
    #             units=F('ingredient__measurement_unit'),
    #             total=Sum('amount'),
    #         ).order_by('-total')
    #
    #     return RecipeViewSet.generate_shopping_cart_pdf(items, request.user)