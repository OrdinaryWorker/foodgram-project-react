from django.urls import include, path
from djoser.views import TokenDestroyView, TokenCreateView, UserViewSet
from rest_framework.routers import DefaultRouter


from api.views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagsViewSet,

)
app_name = "api"

router = DefaultRouter()

router.register(r"tags", TagsViewSet, basename="tags")
router.register(r"ingredients", IngredientViewSet, basename="ingredients")
router.register(r"recipes", RecipeViewSet, basename="recipes")


auth_patterns = [
    path(r"token/login/",
         TokenCreateView.as_view(),
         name="login"
         ),
    path(r"token/logout/",
         TokenDestroyView.as_view(),
         name="logout"
         ),
]

users_patterns = [
    path(r"",
         UserViewSet.as_view({"get": "list", "post": "create"}),
         name="users"
         ),
    path(r"<int:id>/",
         UserViewSet.as_view({"get": "retrieve"}),
         name="user-detail"
         ),
    path(r"me/",
         UserViewSet.as_view({"get": "me"}),
         name="me-detail"
         ),
    path(
        r"set_password/",
        CustomUserViewSet.as_view({"post": "set_password"}),
        name="set-password",
        ),
    path(
        r"subscriptions/",
        CustomUserViewSet.as_view({"get": "list"}),
        name="subscriptions",
        ),
    path(
        r"<int:author_id>/subscribe/",
        CustomUserViewSet.as_view(
            {"post": "create", "delete": "destroy"}),
        name="subscribe",
        ),
]


urlpatterns = [
    path(r"auth/", include(auth_patterns)),
    path(r"users/", include(users_patterns)),
    path(r"", include(router.urls)),
]


