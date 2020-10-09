from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from server.utils.cmaps import AVAILABLE_CMAPS
from server.serializers import ColormapSerializer
from server.utils.profile import trace

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from typing import List, Tuple, TypeVar, Dict, Any

import numpy as np

Number = TypeVar('Number', int, float)

class ColormapViewSet(viewsets.ViewSet):
    renderer_classes=[JSONRenderer]

    stretch_min_param = openapi.Parameter(
        'stretch_min',
        openapi.IN_QUERY,
        description="Minimum stretch range value",
        type=openapi.TYPE_NUMBER,
        required=True
    )

    stretch_max_param = openapi.Parameter(
        'stretch_max',
        openapi.IN_QUERY,
        description="Maximum stretch range value",
        type=openapi.TYPE_NUMBER,
        required=True
    )

    colormap_param = openapi.Parameter(
        'colormap',
        openapi.IN_QUERY,
        description="String representing colormap to apply to tile",
        required=False,
        type=openapi.TYPE_STRING,
        enum=AVAILABLE_CMAPS
    )

    num_values_param = openapi.Parameter(
        'num_values',
        openapi.IN_QUERY,
        description="Number of Values to return",
        required=True,
        type=openapi.TYPE_INTEGER
    )

    @swagger_auto_schema(
        manual_parameters=[stretch_min_param, stretch_max_param, colormap_param, num_values_param],
        operation_id="colormap"
    )
    def retrieve(self, request, stretch_min: Number = None, stretch_max: Number = None,
                 colormap: str = None, num_values: int = 255) -> List[Dict[str, Any]]:
        """Returns a list [{value=pixel value, rgba=rgba tuple}] for given stretch parameters"""
        from server.utils import image

        params = ColormapSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data

        colormap = data.get('colormap', None)
        stretch_min = data.get('stretch_min', None)
        stretch_max = data.get('stretch_max', None)
        num_values = data.get('num_values', None)

        stretch_range = [stretch_min, stretch_max]
        
        target_coords = np.linspace(stretch_min, stretch_max, num_values)

        if colormap is not None:
            from server.utils.cmaps import get_cmap
            cmap = get_cmap(colormap)
        else:
            # assemble greyscale cmap of shape (255, 4)
            cmap = np.ones(shape=(255, 4), dtype='uint8') * 255
            cmap[:, :-1] = np.tile(np.arange(1, 256, dtype='uint8')[:, np.newaxis], (1, 3))

        cmap_coords = image.to_uint8(target_coords, *stretch_range) - 1
        colors = cmap[cmap_coords]
        values = [dict(value=p, rgba=c) for p, c in zip(target_coords.tolist(), colors.tolist())]
        payload = {'colormap': values}
        return Response(payload)