from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from server.models import Dataset, DatasetStats
from server.serializers import SinglebandSerializer
from server.renderers import PNGRenderer
from server.utils.cmaps import AVAILABLE_CMAPS
from server.utils import xyz, image
from server.utils.raster_base import RasterDriver

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from config.settings import DEFAULT_TILE_SIZE

from typing import Mapping, Union, Tuple, TypeVar
from typing.io import BinaryIO

import collections

Number = TypeVar('Number', int, float)
RGBA = Tuple[Number, Number, Number, Number]

# AVAILABLE_DATASETS = Dataset.objects.all()

class Singleband(viewsets.ViewSet):
    """
    Return singleband image as PNG
    """
    renderer_classes = [PNGRenderer]

    # Manually Defined Parameter Schemas
    id_param = openapi.Parameter(
        'id',
        openapi.IN_PATH,
        description="A unique integer value identifying a dataset.",
        required=True,
        type=openapi.TYPE_INTEGER
    )

    z_param = openapi.Parameter(
        'z',
        openapi.IN_PATH,
        description="Tile Zoom value.",
        required=True,
        type=openapi.TYPE_INTEGER
    )

    x_param = openapi.Parameter(
        'x',
        openapi.IN_PATH,
        description="Tile X Value.",
        required=True,
        type=openapi.TYPE_INTEGER
    )

    y_param = openapi.Parameter(
        'y',
        openapi.IN_PATH,
        description="Tile Y Value.",
        required=True,
        type=openapi.TYPE_INTEGER
    )

    colormap_param = openapi.Parameter(
        'colormap',
        openapi.IN_QUERY,
        description="String representing colormap to apply to tile.",
        required=False,
        type=openapi.TYPE_STRING,
        enum=AVAILABLE_CMAPS
    )

    stretch_min_param = openapi.Parameter(
        'stretch_min',
        openapi.IN_QUERY,
        description="Minimum stretch range value.",
        type=openapi.TYPE_NUMBER,
        required=False
    )

    stretch_max_param = openapi.Parameter(
        'stretch_max',
        openapi.IN_QUERY,
        description="Maximum stretch range value.",
        type=openapi.TYPE_NUMBER,
        required=False
    )

    tile_size_param = openapi.Parameter(
        'tile_size',
        openapi.IN_QUERY,
        description="Pixel dimensions of the returned PNG image as JSON list.",
        type=openapi.TYPE_INTEGER,
        required=False
    )


    @swagger_auto_schema(
        manual_parameters=[id_param, z_param, x_param, y_param, colormap_param,
                           stretch_min_param, stretch_max_param, tile_size_param],
        operation_id="singleband (tile)"
    )
    def retrieve(self, request, pk: int = None, 
                 z: int = None, x: int = None, y: int = None,
                 colormap: Union[str, Mapping[Number, RGBA], None] = None,
                 stretch_min: Number = None, stretch_max: Number = None,
                 tile_size: Tuple[int, int] = None) -> BinaryIO:

        queryset = Dataset.objects.all()
        dataset = get_object_or_404(queryset, pk=pk)
        metadata = DatasetStats.objects.get(dataset=dataset)

        tile_xyz = (x, y, z)
        params = SinglebandSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data

        colormap = data.get('colormap', None)
        stretch_min = data.get('stretch_min', None)
        stretch_max = data.get('stretch_max', None)
        tile_size = data.get('tile_size', None)
        
        if tile_size is None:
            tile_size = DEFAULT_TILE_SIZE
                
        tile_size = (tile_size, tile_size)

        stretch_range = metadata.get_range()
        if stretch_min is not None and stretch_max is not None:
            stretch_range = [stretch_min, stretch_max]
        
        if colormap is None:
            colormap = 'gray'

        preserve_values = isinstance(colormap, collections.Mapping)
        driver = RasterDriver()
        tile_data = xyz.get_tile_data(
           driver, dataset, tile_xyz, tile_size=tile_size, preserve_values=preserve_values
        )
        out = image.to_uint8(tile_data, *stretch_range)

        return Response(image.array_to_png(out, colormap=colormap))

    
    @swagger_auto_schema(
        manual_parameters=[id_param, colormap_param, stretch_min_param, 
                            stretch_max_param, tile_size_param],
        operation_id="singleband (preview)"
    )
    def preview(self, request, pk: int = None,
                 colormap: Union[str, Mapping[Number, RGBA], None] = None,
                 stretch_min: Number = None, stretch_max: Number = None,
                 tile_size: Tuple[int, int] = None) -> BinaryIO:

        queryset = Dataset.objects.all()
        dataset = get_object_or_404(queryset, pk=pk)
        metadata = DatasetStats.objects.get(dataset=dataset)
        tile_xyz = (0, 0, 0)

        params = SinglebandSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data

        colormap = data.get('colormap', None)
        stretch_min = data.get('stretch_min', None)
        stretch_max = data.get('stretch_max', None)
        tile_size = data.get('tile_size', None)

        if tile_size is None:
            tile_size = DEFAULT_TILE_SIZE
            
        tile_size = (tile_size, tile_size)

        stretch_range = metadata.get_range()
        if stretch_min is not None and stretch_max is not None:
            stretch_range = [stretch_min, stretch_max]
        
        if colormap is None:
            colormap = 'gray'

        preserve_values = isinstance(colormap, collections.Mapping)
        driver = RasterDriver()
        tile_data = xyz.get_tile_data(
           driver, dataset, tile_xyz, tile_size=tile_size, preserve_values=preserve_values
        )
        out = image.to_uint8(tile_data, *stretch_range)

        return Response(image.array_to_png(out, colormap=colormap))
