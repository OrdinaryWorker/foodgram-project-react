from djoser.serializers import UserSerializer
from rest_framework import serializers

from users.models import User, Follow


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, author):
        request = self.context['request']
        return (
                request.user.is_authenticated
                and author.following.filter(user=request.user).exists()
        )

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed'
                  )
        read_only_fields = fields


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Follow
        fields = (
            'user',
            'author',
        )

    def validate(self, data):
        user = self.context.get('request').user
        author = self.initial_data.get('author')
        if user == author:
            raise serializers.ValidationError(
                'Пользователь не может подписаться на самого себя!'
            )
        if author.following.filter(user=user).exists():
            raise serializers.ValidationError(
                'Нельзя подписаться дважды на одного пользователя!'
            )
        return data
