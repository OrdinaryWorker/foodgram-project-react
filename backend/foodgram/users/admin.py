from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Follow, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    @admin.display(description='Количество подписчиков')
    def followers_amount(self, user):
        """Количество подписчиков для вывода в админке."""
        return user.followers.count()
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'is_staff',
        'is_superuser',
        'followers_amount',
    )
    list_filter = (
        'is_superuser',
        'is_staff',
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ("Персональная информация", {'fields': ('username',
                                                'first_name',
                                                'last_name',
                                                )
                                     },
         ),
        ('Права доступа', {'fields': ('is_active',
                                      'is_superuser',
                                      'is_staff',
                                      )
                           },
         ),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide', ),
                'fields': ('email', 'password1', 'password2'),
            },
        ),
    )
    search_fields = (
        'username',
        'email',
    )
    ordering = ('email',)
    filter_horizontal = ()
    empty_value_display = settings.ADMIN_MODEL_EMPTY_VALUE


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'author',
    )
    search_fields = (
        'author',
        'user',

    )
    list_filter = (
        'author',
        'user',
    )
    empty_value_display = settings.ADMIN_MODEL_EMPTY_VALUE
