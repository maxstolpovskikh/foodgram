from django.core.exceptions import ValidationError
from rest_framework import serializers
from tags.serializers import TagSerializer
from users.serializers import CustomUserSerializer

from api.services import Base64ImageField
from .models import Ingredient, Recipe, RecipeIngredient, Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipeingredient_set'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time',
        )
        read_only_fields = (
            'is_favorite',
            'is_shopping_cart',
        )

    def validate(self, data):
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')
        cooking_time = self.initial_data.get('cooking_time')

        if cooking_time < 1:
            raise ValidationError('Слишком быстро')

        if not tags or not ingredients:
            raise ValidationError("Недостаточно данных")

        item_list = []
        for item in ingredients:
            if item['amount'] < 1:
                raise ValidationError('Кол-во меньше 1')
            if item['id'] in item_list:
                raise ValidationError('Повторяющиеся ингридиенты')
            item_list.append(item['id'])

        if len(tags) != len(set(tags)):
            raise ValidationError('Повторяющиеся теги')

        for tag in tags:
            try:
                tag = Tag.objects.get(id=tag)
            except Tag.DoesNotExist:
                raise ValidationError('Несуществующий тег')

        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('recipeingredient_set')
        tags = self.initial_data.get('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        tags = self.initial_data.get('tags')
        instance.tags.set(tags)
        instance.ingredients.clear()
        ingredients = self.initial_data.get('ingredients')
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient_id = ingredient['id']
            ingredient_obj = Ingredient.objects.get(id=ingredient_id)
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient_obj,
                amount=amount
            )
        return instance

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.shopping_cart.filter(user=request.user).exists()
        return False
