from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views.collections import CollectionViewSet
from .views.datasets import DatasetViewSet
from .views.singleband import Singleband
from .views.colormap import ColormapViewSet
from .views.metadata import DatasetStatsViewSet
from .views.rgb import RGB
from .views.tags import TagViewSet
from .views.demo import demo


singleband_view = Singleband.as_view({
    'get': 'retrieve'
})

singleband_preview_view = Singleband.as_view({
    'get': 'preview'
})

colormap_view = ColormapViewSet.as_view({
    'get': 'retrieve'
})

rgb_view = RGB.as_view({
    'get': 'retrieve'
})

rgb_preview_view = RGB.as_view({
    'get': 'preview'
})

router = DefaultRouter()
router.register(r'collections', CollectionViewSet)
router.register(r'datasets', DatasetViewSet)
router.register(r'metadata', DatasetStatsViewSet)
router.register(r'tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('singleband/<int:pk>/<int:z>/<int:x>/<int:y>.png', singleband_view, name='singleband'),
    path('singleband/<int:pk>/preview.png', singleband_preview_view, name='singleband-preview'),
    path('rgb/<int:r_id>/<int:g_id>/<int:b_id>/<int:z>/<int:x>/<int:y>.png', rgb_view, name='rgb'),
    path('rgb/<int:r_id>/<int:g_id>/<int:b_id>/preview.png', rgb_preview_view, name='rgb'),
    path('colormap', colormap_view, name='colormap'),
    path('demo', demo, name='demo')
]

schema_view = get_schema_view(
    openapi.Info(
        title="Terracotta Django API",
        default_version='v0',
        description="A modern XYZ Tile Server in Python",
    ),
    public=True,
    patterns=[path('', include(urlpatterns))],
)

urlpatterns += [
    # path('swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc', schema_view.with_ui('redoc', cache_timeout=0), name="schema-redoc"),
]