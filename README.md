# adp.py
![Title](images/ADP_find_table_gallery_modes.png)
_ANY DUPLICATED PHOTOS?_ or _adp.py_ is a simple-to-use python module that let you quickly find and delete duplicated photos in a desktop/laptop.

## How To Use It?

### As an application: ###
You can run it as an application using the following terminal command with its optional arguments:

    python3 -m adp  [-h] 
                    [-m or --mode {f,t,g}]  Run in either 'f=find', 't=table' or 'g=gallery' mode.
                    [-l or --layout {h,v}]  Set GUI to use either a 'h=horizontal' or 'v=vertical' layout.
                    [-c or --cfe {p,t}]  Set the concurrent.future.Executor to either 'p=process' or 't=thread' type.

### As a library: ###
You can import the relevant class or functions into your own python script: 

    from adp import {class or function}

#### Accessible classes: ####

    Custom tkinter.ttk widgets: 'ADPFind', 'ADPGallery', 'ADPTable', 'AutoScrollbar', 'DonutCharts', 'DupGroup', 'Find', 'Findings', 'Gallery', 'Progressbarwithblank', 'Table', 'VerticalScrollFrame'
    Others:                     'HyperlinkManager', 'RasterImage'

#### Accessible functions: ####

    For working with tkinter.ttk widgets: 'customise_ttk_widgets_style', 'get_geometry_values','get_thumbnail', 'get_thumbnails_concurrently_with_queue', 'filesize', 'sort_photos_by_creation_time', 'str_geometry_values', 'string_pixel_size', 'stylename_elements_options', 'timings'  
    For finding sub-directories:          'fast_scandir'
    For finding photos:                   'dataklass', 'fast_scandir', 'rscandir_images', 'scandir_images', 'scandir_images_concurrently', 'tuple_rscandir_images', 'tuple_scandir_images'  
    For detecting duplicated photos:      'detect_duplicates_concurrently', 'detect_duplicates_serially'

## OS Prerequisites:
- Linux (tested on Ubuntu 22.04.4, Linux 6.5.0-26-generic, x86_64)
- Windows and MacOS (not tested)

## Dependencies
Execution of this respositry's source code requires your system to have _Python3_, _NumPy_, _Pillow_ installed. For details please see `Pipfile`, `Pipfile.lock` and `requirement.txt`.

## How To Install?
- Recommended: Follow the [Example pipenv Workflow](https://pipenv-fork.readthedocs.io/en/latest/basics.html#example-pipenv-workflow) example.
- If instead you want to use the `pip` command, you have to clone/create this repository to your computer, `cd` to it and run the following command:

      pip install -r requirements.txt