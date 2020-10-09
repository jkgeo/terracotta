from django.utils.decorators import method_decorator

from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from server.models import Collection, Tag
from server.serializers import CollectionSerializer
from server.filters import CollectionTagFilter

# tags = Tag.objects.all()
# AVAILABLE_TAGS = list()
# for t in tags:
#     AVAILABLE_TAGS.append(t.name)

tag_param = openapi.Parameter(
    'tag',
    openapi.IN_QUERY,
    description="String representing tag(s) to filter collections.",
    required=False,
    type=openapi.TYPE_STRING,
    # enum=AVAILABLE_TAGS
)

class CollectionPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'limit'


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_id="collection list", manual_parameters=[tag_param]
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_id="collection detail"
))
class CollectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    pagination_class = CollectionPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CollectionTagFilter
    search_fields = ['name', 'metadata', 'tags__name']