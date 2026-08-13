"""Scrittore PSD minimale: livelli RGBA non compressi, 8 bit, RGB.

Genera file apribili con GIMP e Photoshop mantenendo i livelli separati.
"""
import struct
import numpy as np


def _pascal4(s):
    """Pascal string (1 byte len + testo) con padding a multiplo di 4."""
    b = s.encode("latin-1", "replace")[:255]
    out = bytes([len(b)]) + b
    pad = (-len(out)) % 4
    return out + b"\x00" * pad


def _luni(name):
    """Blocco '8BIM'/'luni': nome livello in UTF-16BE (per accenti e nomi lunghi)."""
    chars = name.encode("utf-16-be")
    data = struct.pack(">I", len(name)) + chars
    if len(data) % 2:
        data += b"\x00"
    return b"8BIM" + b"luni" + struct.pack(">I", len(data)) + data


def _resource_block(res_id, data):
    body = b"8BIM" + struct.pack(">H", res_id) + b"\x00\x00" + struct.pack(">I", len(data))
    if len(data) % 2:
        data += b"\x00"
    return body + data


def _resolution_resource(dpi):
    fixed = int(round(dpi * 65536))
    # hRes, hResUnit(1=px/inch), widthUnit(2=cm), vRes, vResUnit, heightUnit
    data = struct.pack(">IHHIHH", fixed, 1, 2, fixed, 1, 2)
    return _resource_block(1005, data)


def _bbox(alpha):
    """Bounding box dei pixel non trasparenti, o None se il livello e' vuoto."""
    ys, xs = np.nonzero(alpha)
    if len(ys) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def write_psd(path, width, height, layers, dpi=300, background=(255, 255, 255)):
    """layers: lista di dict {name, image (RGBA np.uint8 HxWx4), visible}

    Il primo livello della lista e' il piu' in basso nello stack.
    """
    # ---- composito appiattito (per anteprima negli editor) ----
    comp = np.zeros((height, width, 3), dtype=np.float64)
    comp[:, :] = background
    for layer in layers:
        if not layer.get("visible", True):
            continue
        img = layer["image"].astype(np.float64)
        a = (img[:, :, 3:4]) / 255.0
        comp = img[:, :, :3] * a + comp * (1 - a)
    comp = np.clip(comp, 0, 255).astype(np.uint8)

    # ---- header ----
    out = bytearray()
    out += b"8BPS" + struct.pack(">H", 1) + b"\x00" * 6
    out += struct.pack(">HIIHH", 3, height, width, 8, 3)

    # ---- color mode data (vuoto per RGB) ----
    out += struct.pack(">I", 0)

    # ---- image resources: risoluzione ----
    resources = _resolution_resource(dpi)
    out += struct.pack(">I", len(resources)) + resources

    # ---- layer and mask information ----
    records = bytearray()
    chan_data = bytearray()

    for layer in layers:
        img = layer["image"]
        box = _bbox(img[:, :, 3])
        if box is None:
            box = (0, 0, 1, 1)
        left, top, right, bottom = box
        crop = img[top:bottom, left:right]
        h, w = crop.shape[0], crop.shape[1]

        records += struct.pack(">iiii", top, left, bottom, right)
        records += struct.pack(">H", 4)
        # canali: -1 alpha, 0 R, 1 G, 2 B. Ogni lunghezza include i 2 byte di compressione.
        per_channel = 2 + w * h
        for cid in (-1, 0, 1, 2):
            records += struct.pack(">hI", cid, per_channel)

        flags = 0x00 if layer.get("visible", True) else 0x02
        records += b"8BIM" + b"norm" + bytes([255, 0, flags, 0])

        extra = bytearray()
        extra += struct.pack(">I", 0)          # layer mask data: assente
        extra += struct.pack(">I", 0)          # blending ranges: assenti
        extra += _pascal4(layer["name"])
        extra += _luni(layer["name"])
        if len(extra) % 2:
            extra += b"\x00"
        records += struct.pack(">I", len(extra)) + bytes(extra)

        # dati canale: alpha, R, G, B, ciascuno preceduto da compressione 0 (raw)
        for idx in (3, 0, 1, 2):
            chan_data += struct.pack(">H", 0)
            chan_data += crop[:, :, idx].tobytes()

    layer_info = struct.pack(">h", len(layers)) + bytes(records) + bytes(chan_data)
    if len(layer_info) % 2:
        layer_info += b"\x00"

    layer_and_mask = struct.pack(">I", len(layer_info)) + layer_info
    layer_and_mask += struct.pack(">I", 0)  # global layer mask info
    out += struct.pack(">I", len(layer_and_mask)) + layer_and_mask

    # ---- image data: composito, raw planare ----
    out += struct.pack(">H", 0)
    for c in range(3):
        out += comp[:, :, c].tobytes()

    with open(path, "wb") as fh:
        fh.write(bytes(out))
    return len(out)
