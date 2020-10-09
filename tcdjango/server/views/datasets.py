from django.utils.decorators import method_decorator
from django.core import serializers

from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from server.models import Dataset, Collection, Tag
from server.serializers import DatasetSerializer
from server.filters import DatasetTagFilter

# collections = Collection.objects.all()
# AVAILABLE_COLLECTIONS = list()
# for c in collections:
#     AVAILABLE_COLLECTIONS.append(c.slug)

# tags = Tag.objects.all()
# AVAILABLE_TAGS = list()
# for t in tags:
#     AVAILABLE_TAGS.append(t.name)

class DatasetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'limit'

collection_param = openapi.Parameter(
    'collection',
    openapi.IN_QUERY,
    description="String representing Collection of desired dataset(s).",
    required=False,
    type=openapi.TYPE_STRING,
    # enum=AVAILABLE_COLLECTIONS
)

tag_param = openapi.Parameter(
    'tag',
    openapi.IN_QUERY,
    description="String representing tag(s) to filter datasets.",
    required=False,
    type=openapi.TYPE_STRING,
    # enum=AVAILABLE_TAGS
)

@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_id="dataset list", manual_parameters=[collection_param, tag_param]
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_id="dataset detail"
))
class DatasetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    pagination_class = DatasetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = DatasetTagFilter
    search_fields = ['name', 'metadata', 'tags__name']