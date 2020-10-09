import os, argparse, glob, json
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File

from server.utils.raster_base import RasterDriver
from server.models import Collection, Dataset, DatasetStats

import tqdm
import rasterio

class Command(BaseCommand):
    help = 'Ingest raster files'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='+', help='Path of a file or directory of files to ingest.')
        parser.add_argument('-c', '--collection', type=int, help='ID of collection to add dataset(s) to. Otherwise will be added to default collection')

    def handle(self, *args, **options):
        path = options['path']

        if options['collection']:
            collection_id = options['collection']
            collection = Collection.objects.get(id=collection_id)
        else:
            collection, collection_created = Collection.objects.get_or_create(default=True, defaults={'name':'Default Collection'}) 
            if collection_created:
                self.stdout.write('New Collection Created')

        full_paths = [os.path.join(os.getcwd(), p) for p in path]
        files = list()

        for path in full_paths:
            if os.path.isfile(path):
                files.append(path)
            else:
                full_paths += glob.glob(path + '/*')

        for f in tqdm.tqdm(files):
            try:
                rasterio.open(f)
            
                base_file = os.path.basename(f)
                fileName, fileExt = os.path.splitext(base_file)
                self.stdout.write(f"Calculating {base_file} Stats...")
                image_stats = RasterDriver.compute_metadata(f)
                dataset_stats = DatasetStats(
                    bounds_north=image_stats['bounds'][0],
                    bounds_east=image_stats['bounds'][1],
                    bounds_south=image_stats['bounds'][2],
                    bounds_west=image_stats['bounds'][3],
                    convex_hull=image_stats['convex_hull'],
                    valid_percentage=image_stats['valid_percentage'],
                    min=image_stats['range'][0],
                    max=image_stats['range'][1],
                    mean=image_stats['mean'],
                    stdev=image_stats['stdev'],
                    percentiles=image_stats['percentiles']            
                )
                dataset_stats.save()

                new_dataset = Dataset(collection=collection, name=fileName, stats=dataset_stats)
                
                with open(f, 'rb') as file_object:
                    new_dataset.filepath = File(file_object, name=os.path.basename(file_object.name))
                    self.stdout.write(f"Saving {base_file}...")
                    new_dataset.save()
    
                self.stdout.write(f"Successfully Ingested {base_file}.")
            except :
                self.stderr.write(f'Skipping {f}, unable to open or not a recognized raster format.')
                files.remove(f)
                pass
