from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from server.models import Dataset, DatasetStats
from server.serializers import RGBSerializer
from server.renderers import PNGRenderer
from server.utils.cmaps import AVAILABLE_CMAPS
from server.utils import xyz, image
from server.utils.raster_base import RasterDriver

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from config.settings import DEFAULT_TILE_SIZE

from typing import Mapping, Union, Tuple, TypeVar
from typing.io import BinaryIO
from concurrent.futures import Future

import collections

Number = TypeVar('Number', int, float)
RGBA = Tuple[Number, Number, Number, Number]

class RGB(viewsets.ViewSet):
    """
    Return singleband image as PNG
    """
    renderer_classes = [PNGRenderer]

    # Manually Defined Parameter Schemas
    r_id_param = openapi.Parameter(
        'r_id',
        openapi.IN_PATH,
        description="A unique integer value identifying a dataset for the red band.",
        required=True,
        type=openapi.TYPE_INTEGER
    )

    g_id_param = openapi.Parameter(
        'g_id',
        openapi.IN_PATH,
        description="A unique integer value identifying a dataset for the green band.",
        required=True,
        type=openapi.TYPE_INTEGER
    )

    b_id_param = openapi.Parameter(
        'b_id',
        openapi.IN_PATH,
        description="A unique integer value identifying a dataset for the blue band.",
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
        manual_parameters=[r_id_param, g_id_param, b_id_param,
                           z_param, x_param, y_param,
                           stretch_min_param, stretch_max_param, tile_size_param],
        operation_id="rgb (tile)"
    )
    def retrieve(self, request, r_id: int = None, g_id: int = None, b_id: int = None,
                 z: int = None, x: int = None, y: int = None,
                 stretch_min: Number = None, stretch_max: Number = None,
                 tile_size: Tuple[int, int] = None) -> BinaryIO:
        
        import numpy as np

        queryset = Dataset.objects.all()
        r_dataset = get_object_or_404(queryset, pk=r_id)
        g_dataset = get_object_or_404(queryset, pk=g_id)
        b_dataset = get_object_or_404(queryset, pk=b_id)
        metadata = DatasetStats.objects.get(dataset=r_dataset)
        rgb_values = (r_id, g_id, b_id)
        tile_xyz = (x, y, z)
        params = RGBSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data

        stretch_min = data.get('stretch_min', None)
        stretch_max = data.get('stretch_max', None)
        tile_size = data.get('tile_size', None)

        if tile_size is None:
            tile_size = DEFAULT_TILE_SIZE

        stretch_range = metadata.get_range()
        if stretch_min is not None and stretch_max is not None:
            stretch_range = [stretch_min, stretch_max]
        
        stretch_ranges_ = [stretch_range, stretch_range, stretch_range]

        driver = RasterDriver()

        def get_band_future(band_id: int) -> Future:
            dataset = get_object_or_404(queryset, pk=band_id)
            return xyz.get_tile_data(driver, dataset, tile_xyz,
                                     tile_size=tile_size, asynchronous=True)

        futures = [get_band_future(band_id) for band_id in rgb_values]
        band_items = zip(rgb_values, stretch_ranges_, futures)

        out_arrays = []

        for i, (band_key, band_stretch_override, band_data_future) in enumerate(band_items):
            band_data = band_data_future.result()
            out_arrays.append(image.to_uint8(band_data, *band_stretch_override))
        
        out = np.ma.stack(out_arrays, axis=-1)
        print(out)
        return Response(image.array_to_png(out))

    
    @swagger_auto_schema(
        manual_parameters=[r_id_param, g_id_param, b_id_param,
                           stretch_min_param, stretch_max_param, tile_size_param],
        operation_id="rgb (preview)"
    )
    def preview(self, request, r_id: int = None, g_id: int = None, b_id: int = None,
                stretch_min: Number = None, stretch_max: Number = None,
                tile_size: Tuple[int, int] = None) -> BinaryIO:
        
        import numpy as np

        queryset = Dataset.objects.all()
        r_dataset = get_object_or_404(queryset, pk=r_id)
        g_dataset = get_object_or_404(queryset, pk=g_id)
        b_dataset = get_object_or_404(queryset, pk=b_id)
        metadata = DatasetStats.objects.get(dataset=r_dataset)
        rgb_values = (r_id, g_id, b_id)
        tile_xyz = (0, 0, 0)
        params = RGBSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data

        stretch_min = data.get('stretch_min', None)
        stretch_max = data.get('stretch_max', None)
        tile_size = data.get('tile_size', None)

        if tile_size is None:
            tile_size = DEFAULT_TILE_SIZE

        stretch_range = metadata.get_range()
        if stretch_min is not None and stretch_max is not None:
            stretch_range = [stretch_min, stretch_max]
        
        stretch_ranges_ = [stretch_range, stretch_range, stretch_range]

        driver = RasterDriver()

        def get_band_future(band_id: int) -> Future:
            dataset = get_object_or_404(queryset, pk=band_id)
            return xyz.get_tile_data(driver, dataset, tile_xyz,
                                     tile_size=tile_size, asynchronous=True)

        futures = [get_band_future(band_id) for band_id in rgb_values]
        band_items = zip(rgb_values, stretch_ranges_, futures)

        out_arrays = []

        for i, (band_key, band_stretch_override, band_data_future) in enumerate(band_items):
            band_data = band_data_future.result()
            out_arrays.append(image.to_uint8(band_data, *band_stretch_override))
        
        out = np.ma.stack(out_arrays, axis=-1)
        print(out)
        return Response(image.array_to_png(out))