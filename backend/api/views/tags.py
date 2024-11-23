from rest_framework import viewsets

from tags.models import Tag
from api.serializers.tags import TagSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
