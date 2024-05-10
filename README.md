# adp.py
![Title](docs/images/ADP_find_table_gallery_modes.png)
`adp` (_"ANY DUPLICATED PICTURES?"_) is a simple-to-use, mini-sized, Python module that let's you quickly find and delete duplicated picture files in a desktop/laptop. All you have to do is to click the <kbd>Folder</kbd> button to select a folder that you want to search, followed by clicking on the <kbd>Find</kbd> button to search it and all its subfolders for duplicated pictures. Once completed, you can click on the duplicated pictures you want to delete and finally click on the <kbd>Delete</kbd> button to delete them. `adp.py` is only 1.2 MB in size, so it is fast to download and install. 

Notes: 
1. _Original_ denotes the earliest version of a duplicate picture and is colour coded in green. _Copies_ denotes its later versions and is colour coded in blue. Clicking the <kbd>Originals</kbd> or <kbd>Copies</kbd> buttons toggles their quick selection/deselection.
2. To manually select/deselect multiple picture files, press the <kbd>Shift</kbd> key in your keyboard followed by clicking the first and last file paths with your mouse pointer. You can also select/deselect a single picture file by simply clicking on its filepath or thumbnail-image.
3. Using `cfe=process` is much faster than `cfe=thread` as it involves using a pool of your CPU logical cores (i.e. process-pool) vs a pool of CPU threads (i.e. thread-pool) to find pictures and their duplicates. That is why `ADP` defaults to using process-pool.
4. The diagram below illustrates just how much faster ADP can be when using many logical cores vs 1 logical core to find pictures and their duplicates in a NVME storage disk. The contrast of faster performance is most obvious when large quantities of large pictures(i.e, high resolution pictures) and their duplicates are processed. Consequently, ADP defaults to using all available CPU logical cores.

   <p align="center">
     <img src="docs/images/ADP_Performances.png" width=950" alt="Performances">
   </p>

5. If your pictures are in a traditional hard disk (HDD), it is recommended that you transfer your pictures to a SSD or NVME storage disk before using ADP to seacrch them. This is because the performance of a HDD is snail pace compared to a SSD or NVME disk and the high performance from using process or thread pool will be mitigated. Moreover, ADP is set to timeout if a search for pictures or the detection of duplicates exceeds 10 minutess.
6. The maximum "Duplicates Group" number is always one less the quantity of _Original_ pictures. 


## Support This Project
If you like this work, please support it: 
1. If you are from Singapore, Malaysia, Indonesia or Thailand, **PayNow** is available.
2. If you are from other countries, <a href="https://www.buymeacoffee.com/JulianChia" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 30px !important;width: 109px !important;" align="center"></a>.


## How To Install?
1. Clone/create this repository into your computer. 
   1. You can download its zipped version by pressing the <kbd>Code</kbd> button on this webpage and then extract the `adp` folder into your computer. 
   2. Alternatively, you can issue this command in your terminal: 
    
          git clone https://github.com/JulianChia/adp.git

2. Next, go to the downloaded `adp` directory: 

       cd path/to/your/cloned/adp/module

3. Install the `adp` module using this `pipenv` command:  

       pipenv sync

   Note: This command ensures that this adp module and its required packages and dependencies resides only in your user account and the `adp` virtual folder and does not affect or depend on any other installed package(s) in your system. The `pipenv` package must first be installed in your system. If it isn't, you can install it following these [instructions](https://pipenv-fork.readthedocs.io/en/latest/install.html#installing-pipenv).


## How To Run adp.py?

1. You can issue the following terminal command (with/without its optional arguments) from the adp folder:

       pipenv run python3 -m adp  [-m or --mode {g,t,f}]  # Run in either 'gallery', 'table' or 'find' mode. Default is 'gallery'.
                                  [-l or --layout {h,v}]  # Set GUI to use either a 'horizontal' or 'vertical' layout. Default for `gallery` and `table` modes is 'horizontal'. 'find' mode allows 'only vertical' layout. 
                                  [-c or --cfe {p,t}]     # Use CPU 'process' or 'thread' pool for execution. Default is 'process'.
                                  [-h]                    # Get help. 
       
       Examples:
       pipenv run python3 -m adp           # default options: adp -m g -l h -c p 
       pipenv run python3 -m adp -m t      # in 'table' mode
       pipenv run python3 -m adp -m f      # in 'find' mode


## Operating Systems (OS):
- Linux (tested on Ubuntu 22.04.4, Linux 6.5.0-26-generic, x86_64)
- MacOS (tested on Catalina 10.15, Darwin 19.6.0, x86_64)
- Windows (not tested yet but should work; please let me know your issue.)


## Softwares:
- Required: _Python >=3.10_. 
- Dependencies: _NumPy 1.26.4_, _Pillow 10.2.0_ and _Tk 8.6_.

The command `pipenv sync` ensures the installation of these packages. 


## Notes To Python Programmers:

1. You can also use `adp.py` <u>as a library</u>. To access to its classes and/or functions in your python script, use the command: 

       from adp import (classes and/or functions)

   **Accessible classes:**

       Widgets:       ADP, ADPFind, ADPGallery, ADPTable, About, AutoScrollbar, DonutCharts, DupGroup, Find, Findings, Gallery, Progressbarwithblank, Table, VerticalScrollFrame
       For picture:   RasterImage,
       For internet:  HyperlinkManager

   **Accessible functions:**

       For widgets:      customise_ttk_widgets_style, filesize, get_geometry_values, get_thumbnail, get_thumbnail_c, get_thumbnails_concurrently_with_queue, pop_kwargs, sort_pictures_by_creation_time, str_geometry_values, string_pixel_size, stylename_elements_options, timings
       Find subfolders:  fast_scandir
       Find pictures:    dataklass, get_filepaths_in, get_image, get_rasterimages_in_one_folder_concurrently, list_scandir_images, scandir_images, scandir_images_concurrently
       Find duplicates:  detect_duplicates_concurrently, detect_duplicates_serially
       For terminal:     main, percent_complete, show_logo_in_terminal
   Please refer to the source codes for their details.
2. Python script highlights:
   1. Algorithm to search out pictures and their duplicates quickly.
   2. A paging system to view searched results in tkinter widgets with the mousewheel without overflowing memory and with minimal lag.
   3. Stable integration of Python's `threading.Thread`, `concurrent.futures.ProcessPoolExecutor` and `concurrent.futures.ThreadPoolExecutor` objects with tkinter's main event loop. 

