from django_filters import rest_framework as filters
from .models import Collection, Dataset, Tag

class CollectionTagFilter(filters.FilterSet):
    tag = filters.ModelMultipleChoiceFilter(
        field_name='tags__name',
        to_field_name='name',
        label="Tag Name",
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Collection
        fields = []

class DatasetTagFilter(filters.FilterSet):
    collection = filters.ModelChoiceFilter(
        field_name='collection__slug',
        to_field_name='slug',
        label='Collection',
        queryset=Collection.objects.all()
    )

    tag = filters.ModelMultipleChoiceFilter(
        field_name='tags__name',
        to_field_name='name',
        label="Tag Name",
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Dataset
        fields = []