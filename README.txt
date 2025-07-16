README.txt
==========

Overview
--------
These two scripts let you load and view Chang’e mission PDS image files directly from the command line:

  • **change3_image_viewer.py** – for Chang’e-3 data (.2A, .2B, .2C; label is embedded)  
  • **change4-5_image_viewer.py** – for Chang’e-4 and Chang’e-5 data (.2B, .2C with separate .2BL/.2CL labels)

Usage
-----

1. **change3_image_viewer.py**

   - Place `change3_image_viewer.py` and your data entity file (`.2A`, `.2B` or `.2C`) in the same folder.  
     *(No separate label file is needed—labels are embedded in the entity file.)*

   - From a terminal opened in that folder, run:
     ```bash
     python change3_image_viewer.py IMAGE_FILE.2A
     ```
     or
     ```bash
     python3 change3_image_viewer.py IMAGE_FILE.2B
     ```

   - If the script isn’t in the same folder as your data file, give full paths:
     ```bash
     python3 /path/to/change3_image_viewer.py /full/path/to/IMAGE_FILE.2C
     ```

   - **Example:**
     ```bash
     python change3_image_viewer.py CE3_GRAS_TC_I.2A
     ```

2. **change4-5_image_viewer.py**

   - Place `change4-5_image_viewer.py`, your entity file (`.2B` or `.2C`), and its matching label file (`.2BL` or `.2CL`) in the same folder.

   - From a terminal opened in that folder, run:
     ```bash
     python change4-5_image_viewer.py IMAGE_FILE.2B
     ```
     or
     ```bash
     python3 change4-5_image_viewer.py IMAGE_FILE.2C
     ```

   - If the script isn’t in the same folder as your files, give full paths:
     ```bash
     python3 /path/to/change4-5_image_viewer.py /data/path/CE4_PC_I.2B
     ```

   - **Example:**
     ```bash
     python change4-5_image_viewer.py CE5_MC_I.2C
     ```

Notes
-----
- You can use either `python` or `python3`, depending on your setup.  
- Filenames and extensions are case-sensitive on most systems—double-check `.2A`, `.2B`, `.2C`, `.2BL`, and `.2CL`.  
- If you pass only the filename (no path), the script assumes it’s in your current working directory.  
- If you pass a path, the script will look there for both entity and (where required) label files.

Output
------
Each script will:

  1. Open a window to display the image.  
  2. Save a PNG version in the same folder, with the same basename (e.g. `CE3_GRAS_TC_I.png`).
