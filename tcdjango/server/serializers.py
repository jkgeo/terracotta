from rest_framework import serializers
from .models import Collection, Dataset, DatasetStats, Tag
from server.utils.cmaps import AVAILABLE_CMAPS


class CollectionSerializer(serializers.HyperlinkedModelSerializer):
    datasets = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='dataset-detail'
    )
    tags = serializers.StringRelatedField(many=True)
    class Meta:
        model = Collection
        fields = ['url', 'id', 'name', 'slug', 'desc', 'metadata', 'tags', 'datasets']


class ColormapSerializer(serializers.Serializer):
    stretch_min = serializers.FloatField(required=True)
    stretch_max = serializers.FloatField(required=True)
    colormap = serializers.ChoiceField(choices=AVAILABLE_CMAPS, required=False)
    num_values = serializers.IntegerField(required=True, max_value=255)

    def validate(self, data):
        """
        Check that stretch_min is below stretch_max
        """
        if 'stretch_min' not in data or 'stretch_max' not in data:
            pass
        elif data['stretch_min'] > data['stretch_max']:
            raise serializers.ValidationError("Max Stretch value must be greater than min")
        
        return data


class DatasetSerializer(serializers.HyperlinkedModelSerializer):
    tags = serializers.StringRelatedField(many=True)
    class Meta:
        model = Dataset
        fields = ['url', 'id', 'collection', 'name', 'metadata', 'stats', 'tags', 'filepath']


class DatasetStatsSerializer(serializers.ModelSerializer):
    convex_hull = serializers.JSONField()
    percentiles = serializers.JSONField()
    bounds = serializers.ListField(source='get_bounds')
    range = serializers.ListField(source='get_range')

    class Meta:
        model = DatasetStats
        fields = ['id', 'bounds', 'range', 'mean', 'stdev', 'convex_hull', 'percentiles',]


class SinglebandSerializer(serializers.Serializer):
    stretch_min = serializers.FloatField(required=False)
    stretch_max = serializers.FloatField(required=False)
    colormap = serializers.ChoiceField(choices=AVAILABLE_CMAPS, required=False)
    tile_size = serializers.IntegerField(required=False)

    def validate(self, data):
        """
        Check that stretch_min is below stretch_max
        """
        if 'stretch_min' not in data or 'stretch_max' not in data:
            pass
        elif data['stretch_min'] > data['stretch_max']:
            raise serializers.ValidationError("Max Stretch value must be greater than min")
        
        return data


class RGBSerializer(serializers.Serializer):
    stretch_min = serializers.FloatField(required=False)
    stretch_max = serializers.FloatField(required=False)
    tile_size = serializers.IntegerField(required=False)

    def validate(self, data):
        """
        Check that stretch_min is below stretch_max
        """
        if 'stretch_min' not in data or 'stretch_max' not in data:
            pass
        elif data['stretch_min'] > data['stretch_max']:
            raise serializers.ValidationError("Max Stretch value must be greater than min")
        
        return data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']