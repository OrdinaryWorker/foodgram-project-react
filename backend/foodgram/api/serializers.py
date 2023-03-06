from django.conf import settings
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Follow, User


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, author):
        request = self.context['request']
        return (
                request.user.is_authenticated
                and author.following.filter(user=request.user).exists()
        )

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  )
        read_only_fields = fields


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'password'
                  )


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


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = ('name', 'image', 'cooking_time', 'id')


class UserExtendedSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'recipes',
                  'recipes_count',
                  'is_subscribed'
                  )

        read_only_fields = fields

    def get_recipes(self, obj):
        recipes_limit = self.context.get(
            'recipes_limit',
            settings.DEFAULT_RECIPES_LIMIT)
        recipes = obj.recipes.all()[:recipes_limit]
        return RecipeMinifiedSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source="ingredient",  queryset=Ingredient.objects.all()
    )
    name = serializers.StringRelatedField(
        source="ingredient.name", read_only=True
    )
    measurement_unit = serializers.StringRelatedField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
            'name',
            'measurement_unit'
        )


class IngredientCreateInRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'recipe', 'amount')


class TagsCreateInRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', )


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    image = Base64ImageField(max_length=None, use_url=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        exclude = ('pub_date', )

    def get_ingredients(self, obj):
        return RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=obj).all(), many=True
        ).data


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    author = CustomUserSerializer(required=False)

    class Meta:
        model = Recipe
        exclude = ('pub_date', )

    def validate(self, attrs):
        if len(attrs['tags']) == 0:
            raise serializers.ValidationError(
                'Должен быть выбран хотя бы один тег.'
            )
        if len(attrs['tags']) != len(set(attrs['tags'])):
            raise serializers.ValidationError(
                'Теги должны быть уникальны.'
            )
        if len(attrs['ingredients']) == 0:
            raise serializers.ValidationError(
                'Должен быть выбран хотя бы один ингредиент.'
            )
        ingredients = attrs['ingredients']
        if len(ingredients) != len(
                set(obj['ingredient'] for obj in ingredients)
        ):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальны.'
            )
        if any(obj['amount'] <= 0 for obj in ingredients):
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше нуля.'
            )
        if attrs['cooking_time'] <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше нуля.'
            )
        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        create_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(create_ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.ingredients.clear()

            create_ingredients = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient=ingredient['ingredient'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            ]
            RecipeIngredient.objects.bulk_create(create_ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, obj):
        self.fields.pop('ingredients')
        self.fields['tags'] = TagSerializer(many=True)
        representation = super().to_representation(obj)
        representation['ingredients'] = RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=obj).all(), many=True
        ).data
        return representation
