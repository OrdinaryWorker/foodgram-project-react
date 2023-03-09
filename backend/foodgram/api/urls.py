from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView, UserViewSet
from rest_framework.routers import DefaultRouter

from api.views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                       TagsViewSet)

app_name = 'api'

router = DefaultRouter()

router.register('tags', TagsViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

auth_patterns = [
    path('token/login/',
         TokenCreateView.as_view(),
         name='login'
         ),
    path('token/logout/',
         TokenDestroyView.as_view(),
         name='logout'
         ),
]

users_patterns = [
    path('<int:id>/',
         UserViewSet.as_view({'get': 'retrieve'}),
         name='user-detail'
         ),
    path('me/',
         UserViewSet.as_view({'get': 'me'}),
         name='me-detail'
         ),
    path(
        'set_password/',
        CustomUserViewSet.as_view({'post': 'set_password'}),
        name='set-password',
        ),
    path(
        'subscriptions/',
        CustomUserViewSet.as_view({'get': 'list'}),
        name='subscriptions',
        ),
    path(
        '<int:author_id>/subscribe/',
        CustomUserViewSet.as_view(
            {'post': 'create', 'delete': 'destroy'}),
        name='subscribe',
        ),
    path('',
         UserViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='users'
         ),
]

urlpatterns = [
    path('auth/', include(auth_patterns)),
    path('users/', include(users_patterns)),
    path('', include(router.urls)),
]
