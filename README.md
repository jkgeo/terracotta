# A Django implementation of [Terracotta](https://github.com/DHI-GRAS/terracotta)

### Why Django?

- To take advantage of Django's Databse support and ORM
  - Supported databases include PostgreSQL, MariaDB, MySQL, Oracle, & SQLite 
- Django Rest Framework - a powerful and flexible toolkit for building Web APIs.

## The Terracotta workflow
#### Remains the same, but scripts are now Django management commands.

### 1. Optimize raster files

```bash
$ ls -lh
total 1.4G
-rw-r--r-- 1 dimh 1049089 231M Aug 29 16:45 S2A_20160724_135032_27XVB_B02.tif
-rw-r--r-- 1 dimh 1049089 231M Aug 29 16:45 S2A_20160724_135032_27XVB_B03.tif
-rw-r--r-- 1 dimh 1049089 231M Aug 29 16:46 S2A_20160724_135032_27XVB_B04.tif
-rw-r--r-- 1 dimh 1049089 231M Aug 29 16:56 S2A_20170831_171901_25XEL_B02.tif
-rw-r--r-- 1 dimh 1049089 231M Aug 29 16:57 S2A_20170831_171901_25XEL_B03.tif
-rw-r--r-- 1 dimh 1049089 231M Aug 29 16:57 S2A_20170831_171901_25XEL_B04.tif

$ python manage.py optimize_rasters *.tif -o optimized/

Optimizing rasters: 100%|██████████████████████████| [05:16<00:00, file=S2A_20170831_...25XEL_B04.tif]
```

### 2. Use whichever database you like (change in /config/settings.py)

```bash
$ python manage.py ingest optimized/*.tif 
Ingesting raster files: 100%|███████████████████████████████████████████| 6/6 [00:49<00:00,  8.54s/it]
```

### 3. Serve it up with Django's built-in server

```bash
$ python manage.py runserver
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 05, 2020 - 23:40:39
Django version 2.2.15, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### 4. Explore the running server

#### Manually

You can use any HTTP-capable client, such as `curl`.
```bash
$ curl localhost:5000/datasets/
[
  {
    "url": "http://localhost:8000/datasets/1/",
    "collection": "http://localhost:8000/collections/1/",
    "name": "S2A_20160724_135032_27XVB_B02.tif",
    "metadata": null,
    "stats": "http://localhost:8000/metadata/1/",
    "filepath": "https://localhost:8000/imagery/default-collection/S2A_20160724_135032_27XVB_B02.tif"
  },
]
```

Modern browsers (e.g. Chrome or Firefox) will render the JSON as a tree.

#### Interactively

With django-rest-framework and drf-yasg, this Django project provies:

- A browsable API at the project root
http://localhost/8000

and interactive api documenation with

- Swagger UI
http://localhost:8000/swagger

or

- Redoc 
http://localhost:8000/redoc


