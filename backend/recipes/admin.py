from django.contrib import admin
from django.db.models import Count

from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Favorite,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            favorites_count=Count('favorites')
        )

    def favorites_count(self, obj):
        return obj.favorites_count

    favorites_count.short_description = 'В избранном'


other_models = [RecipeIngredient, ShoppingCart, Favorite]
for model in other_models:
    admin.site.register(model)
