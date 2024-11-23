from django.urls import include, path
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import DefaultRouter

from api.views.recipes import IngredientViewSet, RecipeViewSet
from api.views.tags import TagViewSet
from api.views.users import AvatarView, CustomUserViewSet

router = DefaultRouter()
router.register('users', CustomUserViewSet)
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)


urlpatterns = [
    path('users/me/avatar/', AvatarView.as_view(), name='user-avatar'),
    path(
        'users/me/',
        CustomUserViewSet.as_view(
            {'get': 'me'},
            permission_classes=[IsAuthenticated]
        )
    ),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
