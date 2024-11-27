from django.contrib.auth import get_user_model
from djoser.serializers import (UserCreateSerializer, UserSerializer,
                                ValidationError)
from rest_framework import serializers

from api.fields import Base64ImageField
from users.models import Subscription
from .minifield import RecipeMinifiedSerializer

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField(default=None)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        if obj:
            return obj.subscribers.filter(user=obj).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
            'recipes',
            'recipes_count'
        )
        read_only_fields = fields

    def validate(self, data):
        request = self.context.get('request')
        author = self.instance
        user = request.user
        method = request.method
        subscription_exists = author.subscribers.filter(user=user).exists()

        if method == 'POST':
            if user == author:
                raise ValidationError(
                    'Нельзя подписаться на самого себя'
                )
            if subscription_exists:
                raise ValidationError(
                    'Вы уже подписаны на этого пользователя'
                )
        if method == 'DELETE' and not subscription_exists:
            raise ValidationError(
                'Подписка не существует'
            )
        return data

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMinifiedSerializer(recipes, many=True).data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)
