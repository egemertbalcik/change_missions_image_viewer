import re
import numpy as np
from PIL import Image
import sys
import os
import string

def read_label_from_file(path):
    """
    If `path` is a standalone .lbl, just read it.
    Otherwise assume the first LABEL_RECORDS*RECORD_BYTES bytes of `path` are
    the ASCII PDS3 label, and extract them.
    """
    # Quick sniff: is it a .lbl?
    if path.lower().endswith('.lbl'):
        with open(path, 'r', encoding='latin-1', errors='ignore') as f:
            return f.read()

    # Otherwise, read embedded label from a .2B/.img file
    text = ''
    with open(path, 'rb') as f:
        # We need to find RECORD_BYTES and LABEL_RECORDS first.
        # So read the first 10 KB or so as Latin-1, then parse those two.
        header = f.read(16_384).decode('latin-1', 'ignore')

        # Pull RECORD_BYTES and LABEL_RECORDS
        m_rb = re.search(r'RECORD_BYTES\s*=\s*(\d+)', header)
        m_lr = re.search(r'LABEL_RECORDS\s*=\s*(\d+)', header)
        if not m_rb or not m_lr:
            raise RuntimeError("Cannot find RECORD_BYTES / LABEL_RECORDS in header")
        record_bytes = int(m_rb.group(1))
        label_records = int(m_lr.group(1))

        # Now rewind and read exactly label_records * record_bytes bytes
        f.seek(0)
        raw_lbl = f.read(record_bytes * label_records)
        text = raw_lbl.decode('latin-1', 'ignore')

    return text

def parse_pds3_label_text(lbl_text, lbl_path_hint):
    """
    Given the full ASCII label text, extract:
      - RECORD_BYTES, LABEL_RECORDS
      - ^IMAGE record pointer
      - LINES, LINE_SAMPLES, SAMPLE_BITS, SAMPLE_TYPE
    """
    meta = {}
    printable = set(string.printable)

    for raw in lbl_text.splitlines():
        # strip comments
        line = raw.split('/*')[0]
        # remove non-printable
        line = ''.join(ch for ch in line if ch in printable).strip()
        if not line or '=' not in line:
            continue
        key, val = [t.strip() for t in line.split('=', 1)]
        val = val.strip('"\'')
        meta[key] = val

    # Mandatory:
    rb = int(meta.get('RECORD_BYTES', 0))
    lr = int(meta.get('LABEL_RECORDS', 0))
    img_rec = int(meta.get('^IMAGE', lr + 1))  # default just after label
    rows = int(meta['LINES'])
    cols = int(meta['LINE_SAMPLES'])
    bits = int(meta['SAMPLE_BITS'])
    stype = meta.get('SAMPLE_TYPE', '')

    # Build image-filename if separate label:
    if lbl_path_hint.lower().endswith('.lbl'):
        raw_img = meta.get('^IMAGE')
        if raw_img and os.path.exists(raw_img):
            img_file = raw_img
        else:
            # Try same base but with .img/.2B
            base = os.path.splitext(lbl_path_hint)[0]
            for ext in ['.img', '.IMG', '.2b', '.2B']:
                cand = base + ext
                if os.path.exists(cand):
                    img_file = cand
                    break
            else:
                raise FileNotFoundError("Cannot locate image file next to label")
    else:
        # Label was embedded, so image is the same file
        img_file = lbl_path_hint

    # Determine numpy dtype
    if bits == 8:
        dtype = np.uint8
    elif bits == 16:
        dtype = '<u2' if 'LSB' in stype.upper() else '>u2'
    else:
        raise ValueError(f"Unsupported SAMPLE_BITS: {bits}")

    offset = (img_rec - 1) * rb

    print(f"🔍 Parsed PDS3 label: {rows}×{cols}, {bits}-bit, dtype={dtype},")
    print(f"   RECORD_BYTES={rb}, LABEL_RECORDS={lr}, IMAGE_RECORD={img_rec}, byte-offset={offset}")
    print(f"   image file → {img_file}")
    return rows, cols, dtype, img_file, offset

def load_pds3_image(img_path, rows, cols, dtype, offset):
    """
    Seek to `offset` in the raw file, read rows*cols pixels, reshape,
    and normalize to 8-bit if needed.
    """
    with open(img_path, 'rb') as f:
        f.seek(offset)
        raw = f.read(rows * cols * np.dtype(dtype).itemsize)

    arr = np.frombuffer(raw, dtype=dtype)
    if arr.size != rows * cols:
        raise ValueError(f"Image size mismatch: got {arr.size}, expected {rows*cols}")
    img = arr.reshape((rows, cols))

    if dtype != np.uint8:
        mn, mx = img.min(), img.max()
        img = ((img - mn) / (mx - mn) * 255).astype(np.uint8)

    return img

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 change3_image_viewer.py PATH_TO_LABEL.lbl  OR  PATH_TO_IMAGE.2A OR PATH_TO_IMAGE.2B OR PATH_TO_IMAGE.2C")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        raise FileNotFoundError(f"No such file: {path}")

    lbl_text = read_label_from_file(path)
    rows, cols, dtype, img_file, offset = parse_pds3_label_text(lbl_text, path)
    img_array = load_pds3_image(img_file, rows, cols, dtype, offset)

    # show & save
    out = Image.fromarray(img_array)
    out.show()
    png = os.path.splitext(img_file)[0] + '.png'
    out.save(png)
    print(f"✅ Saved PNG → {png}")