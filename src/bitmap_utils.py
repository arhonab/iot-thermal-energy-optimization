"""Custom binary BMP file parser for 24-bit thermal heatmap images."""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class BMPImage:
    width: int
    height: int
    bits_per_pixel: int
    compression: int
    image_size: int
    pixels: List[List[Tuple[int, int, int]]]  # 2D grid of (R, G, B) tuples


def read_bmp(file_path: str) -> BMPImage:
    """Parse a 24-bit uncompressed BMP file from raw binary headers."""
    with open(file_path, "rb") as f:
        data = f.read()

    if data[0:2] != b"BM":
        raise ValueError(f"{file_path} is not a valid BMP file.")

    pixel_offset = int.from_bytes(data[10:14], "little")
    width = int.from_bytes(data[18:22], "little")
    height = int.from_bytes(data[22:26], "little")
    bits_per_pixel = int.from_bytes(data[28:30], "little")
    compression = int.from_bytes(data[30:34], "little")
    image_size = int.from_bytes(data[34:38], "little")

    if bits_per_pixel != 24:
        raise ValueError(f"Unsupported bit depth ({bits_per_pixel}-bit); expected 24-bit RGB BMP.")

    # BMP rows are padded to multiples of 4 bytes and stored bottom-to-top
    row_bytes = width * 3
    padding = (4 - (row_bytes % 4)) % 4

    pixels: List[List[Tuple[int, int, int]]] = []
    pos = pixel_offset

    for _ in range(height):
        row: List[Tuple[int, int, int]] = []
        for _ in range(width):
            b = data[pos]
            g = data[pos + 1]
            r = data[pos + 2]
            row.append((r, g, b))
            pos += 3
        pos += padding
        pixels.append(row)

    # Flip vertically so row 0 corresponds to the top of the image
    pixels.reverse()

    return BMPImage(
        width=width,
        height=height,
        bits_per_pixel=bits_per_pixel,
        compression=compression,
        image_size=image_size,
        pixels=pixels,
    )
