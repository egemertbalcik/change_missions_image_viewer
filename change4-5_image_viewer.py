import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
import sys
import os

def parse_pds4_label(lbl_path):
    tree = ET.parse(lbl_path)
    root = tree.getroot()
    ns = {'pds': 'http://pds.nasa.gov/pds4/pds/v1'}

    # width & height
    width  = int(root.find('.//pds:Axis_Array[pds:axis_name="Sample"]/pds:elements', ns).text)
    height = int(root.find('.//pds:Axis_Array[pds:axis_name="Line"]/pds:elements',   ns).text)

    # bands
    band_elem = root.find('.//pds:Axis_Array[pds:axis_name="Band"]/pds:elements', ns)
    bands = int(band_elem.text) if band_elem is not None else 1

    # first try Band_Storage_Type
    bst = root.find('.//pds:Band_Storage_Type', ns)
    if bst is not None and bst.text.strip():
        storage = bst.text.strip().upper()
    else:
        # fallback to Array_3D_Image/axis_index_order
        aio = root.find('.//pds:Array_3D_Image/pds:axis_index_order', ns)
        txt = aio.text.strip().lower() if aio is not None else ''
        # axes seq order = [Line, Sample, Band]
        # "last index fastest" => Band fastest => BIP
        if 'last index fastest' in txt:
            storage = 'BIP'
        else:
            # default to BSQ
            storage = 'BSQ'

    # byte offset
    off_elem = root.find('.//pds:offset', ns)
    offset = int(off_elem.text) if off_elem is not None else 0

    # dtype
    dt = root.find('.//pds:Element_Array/pds:data_type', ns).text
    if   dt == 'UnsignedLSB2': dtype = '<u2'
    elif dt == 'UnsignedMSB2': dtype = '>u2'
    elif dt == 'UnsignedByte':  dtype = np.uint8
    else:
        raise ValueError(f"Unsupported data_type: {dt}")

    print(f"🔍 Parsed → {width}×{height}, bands={bands}, storage={storage}, dtype={dtype}, offset={offset}")
    return width, height, bands, storage, dtype, offset

def load_pds4_image(img_path, w, h, bands, storage, dtype, offset):
    with open(img_path, 'rb') as f:
        f.seek(offset)
        raw = f.read()

    arr = np.frombuffer(raw, dtype=dtype)
    expected = w * h * bands
    if arr.size != expected:
        raise ValueError(f"Expected {expected} samples, got {arr.size}")

    # reshape by storage
    if bands == 1:
        img = arr.reshape((h, w))
    else:
        if storage == 'BIP':
            # H × W × bands
            img = arr.reshape((h, w, bands))
        elif storage == 'BIL':
            # H × bands × W  -> transpose to H×W×bands
            img = arr.reshape((h, bands, w)).transpose(0, 2, 1)
        else:
            # BSQ: bands × H × W -> transpose to H×W×bands
            img = arr.reshape((bands, h, w)).transpose(1, 2, 0)

    # normalize if needed
    if dtype != np.uint8:
        mn, mx = img.min(), img.max()
        img = ((img - mn) / (mx - mn) * 255).astype(np.uint8)

    return img

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 change4-5_image_viewer.py PATH_TO_IMAGE.2B OR PATH_TO_IMAGE.2C")
        sys.exit(1)

    img_file = sys.argv[1]
    lbl_file = img_file + "L"
    if not os.path.exists(img_file) or not os.path.exists(lbl_file):
        raise FileNotFoundError("Both .2B/.2C and .2BL/.2CL must be in the same folder.")

    w, h, b, storage, dt, off = parse_pds4_label(lbl_file)
    arr = load_pds4_image(img_file, w, h, b, storage, dt, off)

    # build PIL image
    if b == 1:
        pil = Image.fromarray(arr, mode='L')
    elif b == 3:
        pil = Image.fromarray(arr, mode='RGB')
    else:
        print(f"⚠️ {b} bands found—displaying first 3")
        pil = Image.fromarray(arr[:, :, :3], mode='RGB')

    pil.show()
    out = os.path.splitext(img_file)[0] + '.png'
    pil.save(out)
    print("✅ Saved PNG:", out)