# +
import argparse as ap
from pathlib import Path

from PIL import Image
import numpy as np

# +
# parser = ap.ArgumentParser()
# parser.add_argument('tileset_image')
# parser.add_argument('tilemap')
# args = parser.parse_args()

base_path = Path('/home/zack/src/slowboy')
tileset_image = base_path / 'tiledata.bmp'
tilemap = base_path / 'tilemap.bin'

# -

tile_image = np.array(Image.open(tileset_image).getdata())
# tile_image.shape
tile_image.dtype


24576 // 8**2
_ // 8

sheet_width = 8
sheet_height = tile_image.shape[0] // sheet_width

# +
tiles = []

for row in range(sheet_height):
    for col in range(sheet_width):
        tiles.append(tile_image[row*8:(row+1)*8,col*8:(col+1)*8,:])
        
tiles
