from django.core.exceptions import ValidationError
from rest_framework import serializers

from api.fields import Base64ImageField
from api.serializers.tags import TagSerializer
from api.serializers.users import CustomUserSerializer
from recipes.models import (MAX_AMOUNT, MIN_AMOUNT, Ingredient, Recipe,
                            RecipeIngredient, Tag)


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
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
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
    cooking_time = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
    )

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

        if not tags:
            raise ValidationError(
                'Нужно добавить минимум один тег'
            )
        if not ingredients:
            raise ValidationError(
                'Нужно добавить минимум один ингредиент'
            )

        if len(ingredients) != len({item['id'] for item in ingredients}):
            raise ValidationError('Повторяющиеся ингридиенты')
        if len(tags) != len(set(tags)):
            raise ValidationError('Повторяющиеся теги')

        for tag in tags:
            try:
                tag = Tag.objects.get(id=tag)
            except Tag.DoesNotExist:
                raise ValidationError('Несуществующий тег')

        return data

    def _get_data(self, validated_data):
        tags = self.initial_data.get('tags')
        ingredients = validated_data.pop('recipeingredient_set')
        return tags, ingredients

    def _create_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ])

    def create(self, validated_data):
        tags, ingredients = self._get_data(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags, ingredients = self._get_data(validated_data)
        instance.tags.set(tags)
        instance.ingredients.clear()
        self._create_ingredients(instance, ingredients)
        return instance

    def _get_is_in_list(self, obj, model_field):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return getattr(obj, model_field).filter(
                user=request.user
            ).exists()
        return False

    def get_is_favorited(self, obj):
        return self._get_is_in_list(obj, 'favorites')

    def get_is_in_shopping_cart(self, obj):
        return self._get_is_in_list(obj, 'shopping_cart')
