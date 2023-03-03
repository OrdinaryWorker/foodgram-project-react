from django.conf import settings
from django.core import validators
from django.db import models
from typing import List, Optional

from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=settings.NAME_MAX_LENGTH,
        help_text='Введите название',
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=settings.UNITS_MAX_LENGTH,
        help_text='Введите единицы измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = (
            'name',
            'measurement_unit',
        )
        constraints = [
            models.UniqueConstraint(
                name='unique_ingredient',
                fields=['name', 'measurement_unit'],
            ),
        ]

    def __str__(self) -> str:
        return f'{self.name}'


class Tag(models.Model):
    name = models.CharField(
        unique=True,
        verbose_name='Название',
        max_length=settings.NAME_MAX_LENGTH,
        help_text='Введите название',
    )
    color = models.CharField(
        verbose_name='Цвет',
        unique=True,
        null=True,
        max_length=settings.COLOR_MAX_LENGTH,
        help_text='Введите цвет в RGB-формате (#rrggbb)',
        validators=[
            validators.RegexValidator(
                r'^#[a-fA-F0-9]{6}$',
                'Используйте RGB-формат для указания цвета (#AABBCC)',
            )
        ],
    )
    slug = models.SlugField(
        verbose_name='Slug',
        unique=True,
        null=True,
        max_length=settings.SLUG_MAX_LENGTH,
        help_text='Введите slug',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class RecipeQuerySet(models.QuerySet):

    def filter_by_tags(self, tags: List[str]):
        if tags:
            return self.filter(tags__slug__in=tags).distinct()
        return self

    def add_user_annotation(self, user_id: Optional[int]):
        return self.annotate(
            is_favorited=models.Exists(
                Favorite.objects.filter(
                    user_id=user_id, recipe__pk=models.OuterRef('pk')
                )
            ),
            is_in_shopping_card=models.Exists(
                ShoppingCart.objects.filter(
                    user_id=user_id, recipe__pk=models.OuterRef('pk')
                )
            )
        )


class Recipe(models.Model):
    pub_date = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
        db_index=True,
        help_text="Автоматически устанавливается текущая дата и время",
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name="Автор",
        help_text="Выберите из списка автора",
    )
    name = models.CharField(
        "Название", max_length=settings.NAME_MAX_LENGTH, help_text="Введите название"
    )
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="recipes/",
        help_text="Выберите картинку",
    )
    text = models.TextField(
        verbose_name="Текстовое описание", help_text="Введите текстовое описание"
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления в минутах",
        help_text="Введите время приготовления в минутах"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        through_fields=('recipe', 'ingredient'),
        verbose_name="Ингредиенты",
        help_text="Выберите ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag, related_name='recipes', verbose_name="Теги", help_text="Выберите теги"
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)

    def __str__(self) -> str:
        return f" {self.name}"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        help_text="Выберите рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент рецепта",
        help_text="Выберите ингредиент рецепта",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество ингредиента",
        help_text="Введите количество ингредиента"
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"

    def __str__(self) -> str:
        return (
            f"{self.ingredient.name} — {self.amount}"
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        help_text="Выберите рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_favorite_user_recipe",
                fields=["user", "recipe"],
            ),
        ]
        verbose_name = "Любимый рецепт"
        verbose_name_plural = "Любимые рецепты"

    def __str__(self):
        return f'Избранный {self.recipe} у {self.user}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name="Рецепт",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_shopping_cart_user_recipe",
                fields=["user", "recipe"],
            ),
        ]
        verbose_name = "Любимый рецепт"
        verbose_name_plural = "Любимые рецепты"

    def __str__(self):
        return f'В списке покупок {self.recipe} у {self.user}'
