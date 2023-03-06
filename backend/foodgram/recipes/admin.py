from django.conf import settings
from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'measurement_unit',
    )
    list_editable = (
        'name',
        'measurement_unit',
    )
    search_fields = (
        'name',
        'measurement_unit',
    )
    list_filter = ('name',)
    empty_value_display = settings.ADMIN_MODEL_EMPTY_VALUE


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'color',
        'slug',
    )
    list_editable = (
        'name',
        'color',
        'slug',
    )
    search_fields = (
        'name',
        'slug',
    )
    list_filter = ('name', )
    empty_value_display = settings.ADMIN_MODEL_EMPTY_VALUE


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1


class FavoriteRecipeInline(admin.TabularInline):
    model = Favorite
    extra = 0


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    @admin.display(description='Добавлений в избранное')
    def favorite_amount(self, obj):
        """Число добавлений рецепта в избранное для вывода в админке."""
        return Favorite.objects.filter(recipe=obj).count()

    @admin.display(description='Ингредиенты')
    def ingredients_in_recipe(self):
        """Ингредиенты рецепта для вывода в админке."""
        return ", ".join(map(str, self.recipeingredient_set.all()))

    list_display = (
        'name',
        'author',
        'pub_date',
        'favorite_amount'
    )
    search_fields = ('name', )
    filter_horizontal = ('tags', )
    list_filter = (
        'tags',
        'author'
    )
    autocomplete_fields = ('ingredients', )
    inlines = (RecipeIngredientInline, )
    readonly_fields = ('favorite_amount', )


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'recipe',
        'ingredient',
        'amount',
    )
    list_editable = ('amount',)
    list_filter = (
        'recipe',
        'ingredient',
    )
    empty_value_display = settings.ADMIN_MODEL_EMPTY_VALUE
