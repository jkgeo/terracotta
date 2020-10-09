from django.contrib import admin
from .models import Collection, Dataset, DatasetStats, Tag

admin.site.register(Collection)
admin.site.register(Dataset)
admin.site.register(DatasetStats)
admin.site.register(Tag)