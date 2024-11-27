from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers.minifield import RecipeMinifiedSerializer
from api.serializers.recipes import IngredientSerializer, RecipeSerializer
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Recipe.objects.prefetch_related('tags').all()
        tags = self.request.query_params.getlist('tags')
        author = self.request.query_params.get('author')
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )

        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        if author:
            queryset = queryset.filter(author=author)
        if is_favorited and self.request.user.is_authenticated:
            if is_favorited == '1':
                queryset = queryset.filter(favorites__user=self.request.user)
        if is_in_shopping_cart and self.request.user.is_authenticated:
            if is_in_shopping_cart == '1':
                queryset = queryset.filter(
                    shopping_cart__user=self.request.user
                )
        return queryset

    def _handle_m2m_action(self, request, pk, model):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        obj = model.objects.filter(user=user, recipe=recipe)

        if request.method == 'POST':
            if obj.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not obj.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        return Response({
            'short-link': f'http://{request.get_host()}/s/{pk}'
        })

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_m2m_action(request, pk, ShoppingCart)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self._handle_m2m_action(request, pk, Favorite)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list = [
            f'{item["ingredient__name"]} '
            f'({item["ingredient__measurement_unit"]}) - '
            f'{item["total_amount"]}'
            for item in ingredients
        ]

        response = HttpResponse(
            'Список покупок:\n\n' + '\n'.join(shopping_list),
            content_type='text/plain'
        )
        response['Content-Disposition'] = 'attachment; filename=shop_list.txt'
        return response
