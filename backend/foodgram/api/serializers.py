from djoser.serializers import UserSerializer

from users.models import User


class CustomUserSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        model = User
