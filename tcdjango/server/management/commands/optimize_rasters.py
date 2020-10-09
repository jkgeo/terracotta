"""scripts/optimize_rasters.py

Convert some raster files to cloud-optimized GeoTiff for use with Terracotta.
"""

from typing import Sequence, Iterator, Union
import os
import glob
import math
import warnings
import itertools
import contextlib
import tempfile
import logging
import pathlib
from pathlib import Path

import tqdm
import rasterio
from rasterio.shutil import copy
from rasterio.io import DatasetReader, MemoryFile
from rasterio.errors import NotGeoreferencedWarning
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.env import GDALVersion
from rasterio.warp import calculate_default_transform

from django.core.management.base import BaseCommand, CommandError
from django.core.files import File

from server.utils.raster_base import RasterDriver
from server.models import Collection, Dataset, DatasetStats

logger = logging.getLogger(__name__)

IN_MEMORY_THRESHOLD = 10980 * 10980

CACHEMAX = 1024 * 1024 * 512  # 512 MB

GDAL_CONFIG = {
    'GDAL_TIFF_INTERNAL_MASK': True,
    'GDAL_TIFF_OVR_BLOCKSIZE': 256,
    'GDAL_CACHEMAX': CACHEMAX,
    'GDAL_SWATH_SIZE': 2 * CACHEMAX
}

COG_PROFILE = {
    'count': 1,
    'driver': 'GTiff',
    'interleave': 'pixel',
    'tiled': True,
    'blockxsize': 256,
    'blockysize': 256,
    'photometric': 'MINISBLACK',
    'ZLEVEL': 1,
    'ZSTD_LEVEL': 9,
    'BIGTIFF': 'IF_SAFER'
}

RESAMPLING_METHODS = {
    'average': Resampling.average,
    'nearest': Resampling.nearest,
    'bilinear': Resampling.bilinear,
    'cubic': Resampling.cubic
}

def GlobbityGlob(raster_files):
    """Expands a glob pattern to Path objects"""
    return [pathlib.Path(f) for f in glob.glob(raster_files)]


# class PathlibPath():
#     """Converts a string to a pathlib.Path object"""

#     def convert(self, *args: Any) -> pathlib.Path:  # type: ignore
#         return pathlib.Path(super().convert(*args))

def _prefered_compression_method() -> str:
    if not GDALVersion.runtime().at_least('2.3'):
        return 'DEFLATE'

    # check if we can use ZSTD (fails silently for GDAL < 2.3)
    dummy_profile = dict(driver='GTiff', height=1, width=1, count=1, dtype='uint8')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', NotGeoreferencedWarning)

            with MemoryFile() as memfile, memfile.open(compress='ZSTD', **dummy_profile):
                pass

    except Exception as exc:
        if 'missing codec' not in str(exc):
            raise
    else:
        return 'ZSTD'

    return 'DEFLATE'


def _get_vrt(src: DatasetReader, rs_method: int) -> WarpedVRT:
    from server.utils.raster_base import RasterDriver
    target_crs = RasterDriver._TARGET_CRS
    vrt_transform, vrt_width, vrt_height = calculate_default_transform(
        src.crs, target_crs, src.width, src.height, *src.bounds
    )
    vrt = WarpedVRT(
        src, crs=target_crs, resampling=rs_method, transform=vrt_transform,
        width=vrt_width, height=vrt_height
    )
    return vrt


@contextlib.contextmanager
def _named_tempfile(basedir: Union[str, Path]) -> Iterator[str]:
    fileobj = tempfile.NamedTemporaryFile(dir=str(basedir), suffix='.tif')
    fileobj.close()
    try:
        yield fileobj.name
    finally:
        os.remove(fileobj.name)


TemporaryRasterFile = _named_tempfile


class Command(BaseCommand):
    help='Optimize a collection of raster files for use with Terracotta.'

    def add_arguments(self, parser):
        parser.add_argument('raster-files', nargs=1, type=str)
        parser.add_argument(
            '-o', '--output-folder', type=str, required=True,
            help='Output folder for cloud-optimized rasters. Subdirectories will be flattened.'
        )
        parser.add_argument(
            '--overwrite', default=False,
            help='Force overwrite of existing files'
        )
        parser.add_argument(
            '--resampling-method', type=str, choices=RESAMPLING_METHODS.keys(),
            default='average', help='Resampling method for overviews (default: %(default)s)'
        )
        parser.add_argument(
            '--reproject', default=False,
            help='Reproject raster file to Web Mercator for faster access (default: %(default)s)'
        )
        parser.add_argument(
            '--in-memory/--no-in-memory', default=None,
            help='Force processing raster in memory / not in memory [default: process in memory '
                f'if smaller than {IN_MEMORY_THRESHOLD // 1e6:.0f} million pixels]'
        )
        parser.add_argument(
            '--compression', default='auto', type=str, choices=['auto', 'deflate', 'lzw', 'zstd', 'none'],
            help='Compression algorithm to use [default: auto (ZSTD if available, DEFLATE otherwise)]'
        )
        parser.add_argument(
            '-q', '--quiet', default=False, help='Suppress all output to stdout'
        )

    def handle(self, *args, **options):

        """Optimize a collection of raster files for use with Terracotta.

        First argument is a list of input files or glob patterns.

        Example:

            $ terracotta optimize-rasters rasters/*.tif -o cloud-optimized/

        Note that all rasters may only contain a single band.
        """

        raster_files = options['raster-files']
        output_folder = pathlib.Path(options['output_folder'])
        resampling_method = options['resampling_method']
        compression = options['compression']
        quiet = options['quiet']
        overwrite = options['overwrite']
        reproject = options['reproject']
        in_memory = None

        full_paths = [os.path.join(os.getcwd(), p) for p in raster_files]
        files = list()

        for path in full_paths:
            if os.path.isfile(path):
                files.append(path)
            else:
                full_paths += glob.glob(path + '/*')

        if not files:
            self.stderr.write('No files given')
            return

        rs_method = RESAMPLING_METHODS[resampling_method]
        
        if compression == 'auto':
            compression = _prefered_compression_method()

        total_pixels = 0
        for f in files:
            if not os.path.isfile(f):
                self.stderr.write(f'Input raster {f!s} is not a file')
            try:
                with rasterio.open(str(f), 'r') as src:
                    if src.count > 1 and not quiet:
                        self.stdout.write(
                            f'Warning: raster file {f!s} has more than one band. '
                            'Only the first one will be used.'
                        )
                    total_pixels += src.height * src.width
            except :
                self.stderr.write(f'Skipping {f}, unable to open or not a recognized raster format.')
                files.remove(f)
                pass

        output_folder.mkdir(exist_ok=True)

        if not quiet:
            # insert newline for nicer progress bar style
            self.stdout.write('')

        sub_pbar_args = dict(
            disable=quiet,
            leave=False,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}'
        )

        with contextlib.ExitStack() as outer_env:
            pbar = outer_env.enter_context(tqdm.tqdm(
                total=total_pixels, smoothing=0, disable=quiet,
                bar_format='{l_bar}{bar}| [{elapsed}<{remaining}{postfix}]',
                desc='Optimizing rasters'
            ))
            outer_env.enter_context(rasterio.Env(**GDAL_CONFIG))

            for input_file in files:
                input_file = pathlib.PurePath(input_file)
                if len(input_file.name) > 30:
                    short_name = input_file.name[:13] + '...' + input_file.name[-13:]
                else:
                    short_name = input_file.name

                pbar.set_postfix(file=short_name)

                output_file = output_folder / input_file.with_suffix('.tif').name

                if not overwrite and output_file.is_file():
                    self.stderr.write(
                        f'Output file {output_file!s} exists (use --overwrite to ignore)'
                    )

                with contextlib.ExitStack() as es, warnings.catch_warnings():
                    warnings.filterwarnings('ignore', message='invalid value encountered.*')

                    src = es.enter_context(rasterio.open(str(input_file)))

                    if reproject:
                        vrt = es.enter_context(_get_vrt(src, rs_method=rs_method))
                    else:
                        vrt = src

                    profile = vrt.profile.copy()
                    profile.update(COG_PROFILE)

                    if in_memory is None:
                        in_memory = vrt.width * vrt.height < IN_MEMORY_THRESHOLD

                    if in_memory:
                        memfile = es.enter_context(MemoryFile())
                        dst = es.enter_context(memfile.open(**profile))
                    else:
                        tempraster = es.enter_context(TemporaryRasterFile(basedir=output_folder))
                        dst = es.enter_context(rasterio.open(tempraster, 'w', **profile))

                    # iterate over blocks
                    windows = list(dst.block_windows(1))

                    for _, w in tqdm.tqdm(windows, desc='Reading', **sub_pbar_args):
                        block_data = vrt.read(window=w, indexes=[1])
                        dst.write(block_data, window=w)
                        block_mask = vrt.dataset_mask(window=w).astype('uint8')
                        dst.write_mask(block_mask, window=w)

                    # add overviews
                    if not in_memory:
                        # work around bug mapbox/rasterio#1497
                        dst.close()
                        dst = es.enter_context(rasterio.open(tempraster, 'r+'))

                    max_overview_level = math.ceil(math.log2(max(
                        dst.height // profile['blockysize'],
                        dst.width // profile['blockxsize'],
                        1
                    )))

                    if max_overview_level > 0:
                        overviews = [2 ** j for j in range(1, max_overview_level + 1)]
                        with tqdm.tqdm(desc='Creating overviews', total=1, **sub_pbar_args):
                            dst.build_overviews(overviews, rs_method)

                        dst.update_tags(ns='rio_overview', resampling=rs_method.value)

                    # copy to destination (this is necessary to push overviews to start of file)
                    with tqdm.tqdm(desc='Compressing', total=1, **sub_pbar_args):
                        copy(
                            dst, str(output_file), copy_src_overviews=True,
                            compress=compression, **COG_PROFILE
                        )

                pbar.update(dst.height * dst.width)