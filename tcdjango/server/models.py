import os
from django.db import models, transaction
from django.core.files.storage import default_storage, FileSystemStorage
from django.utils.text import slugify
from config.storage_backends import ImageryStorage
from config.settings import USE_S3_RASTERS
from jsonfield import JSONField
from .utils.raster_base import RasterDriver

from typing import (Tuple, Dict, Iterator, Sequence, Union,
                    Mapping, Any, Optional, cast, TypeVar, NamedTuple)


if not USE_S3_RASTERS:
    fs = FileSystemStorage(location='media')
elif USE_S3_RASTERS:
    fs = ImageryStorage()


def get_collection_directory(instance, filename):
    return os.path.join(
        instance.collection.slug,
        filename
    )

def generate_unique_slug(instance):
    name = instance.name.replace('.','-')
    base_slug = slugify(name)
    slug = base_slug
    num = 1

    while type(instance).objects.filter(slug=slug).exists():
        slug = f'{base_slug}-{num}'
        num += 1

    unique_slug = slug
    return unique_slug

class Tag(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name


class Collection(models.Model):
    name = models.CharField(max_length=256)
    desc = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True)
    metadata = JSONField(blank=True, null=True)
    slug = models.SlugField(blank=True, unique=True)
    default = models.BooleanField()

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self)

        if not self.default:
            return super(Collection, self).save(*args, **kwargs)
        with transaction.atomic():
            Collection.objects.filter(default=True).update(default=False)
            return super(Collection, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "collection"
    

class DatasetStats(models.Model):
    bounds_north = models.FloatField()
    bounds_east = models.FloatField()
    bounds_south = models.FloatField()
    bounds_west = models.FloatField()
    convex_hull = JSONField()
    valid_percentage = models.FloatField()
    min = models.FloatField()
    max = models.FloatField()
    mean = models.FloatField()
    stdev = models.FloatField()
    percentiles = JSONField()

    def __str__(self):
        return f'{Dataset.objects.get(stats=self.id).name} raster stats'

    def get_bounds(self):
        bounds = (self.bounds_north, self.bounds_east, self.bounds_south, self.bounds_west)
        return bounds

    def get_range(self):
        range = (self.min, self.max)
        return range
    
    class Meta:
        verbose_name = "dataset stats"
        verbose_name_plural = "dataset stats"


class Dataset(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(blank=True, unique=True)
    collection = models.ForeignKey(Collection, related_name='datasets', on_delete=models.CASCADE)
    metadata = JSONField(blank=True, null=True)
    stats = models.OneToOneField(DatasetStats, on_delete=models.PROTECT)
    filepath = models.FileField(upload_to=get_collection_directory, storage=fs)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self)
        super(Dataset, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "dataset"