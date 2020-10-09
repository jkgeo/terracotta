from rest_framework import mixins, viewsets
from server.models import DatasetStats
from server.serializers import DatasetStatsSerializer
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema


@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_id="metadata detail"
))
class DatasetStatsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = DatasetStats.objects.all()
    serializer_class = DatasetStatsSerializer