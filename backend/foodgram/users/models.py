from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.db import models


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    username = models.CharField(
        "Имя пользователя",
        max_length=settings.USERNAME_MAX_LENGTH,
        unique=True,
        help_text=(
            "Введите уникальное имя пользователя. Максимум 40 символов. "
            "Используйте только английские буквы, цифры и символы @/./+/-/_"
        ),
        validators=[ASCIIUsernameValidator()],
        error_messages={
            "unique": "Пользователь с таким именем уже существует",
        },
    )
    email = models.EmailField(
        "Электронная почта",
        max_length=settings.EMAIL_MAX_LENGTH,
        unique=True,
        help_text="Введите адрес электронной почты",
        validators=[ASCIIUsernameValidator()],
        error_messages={
            "unique": "Пользователь с такой почтой уже существует",
        },
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=settings.LAST_NAME_MAX_LENGTH,
        help_text="Введите фамилию"
    )

    first_name = models.CharField(
        "Имя",
        max_length=settings.FIRST_NAME_MAX_LENGTH,
        help_text="Введите имя"
    )

    class Meta:
        ordering = ("email",)
        db_table = "auth_user"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return self.get_username()


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                name='unique_follows',
                fields=['user', 'author'],
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='non_self_follow')
        ]
