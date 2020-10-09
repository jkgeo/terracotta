from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from drf_yasg.utils import swagger_auto_schema

from server.models import Tag
from server.serializers import TagSerializer

from django.utils.decorators import method_decorator


@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_id="tag list"
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_id="tag detail"
))
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name']