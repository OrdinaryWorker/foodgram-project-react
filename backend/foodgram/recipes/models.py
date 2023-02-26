from django.conf import settings
from django.core import validators
from django.db import models


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=settings.NAME_MAX_LENGTH,
        help_text='Введите название',
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=settings.MEASUREMENT_UNIT_MAX_LENGTH,
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
        return f'{self.name} - {self.measurement_unit}'


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

