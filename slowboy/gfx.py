from typing import List, Iterable, Sequence

import sdl2
from sdl2.ext import Color
from sdl2 import (
    SDL_CreateRGBSurfaceWithFormatFrom,
    SDL_ConvertSurfaceFormat,
    SDL_FreeSurface,
    SDL_Error
)

def get_tile_surfaces(tiles, tile_size=(8, 8), format=sdl2.SDL_PIXELFORMAT_RGBA32):
    tile_width, tile_height = tile_size
    rgb_tile = bytearray(tile_width*tile_height*3)
    for tile in tiles:
        for i in range(len(tile)):
            rgb_tile[3*i] = tile[i]
            rgb_tile[3*i+1] = tile[i]
            rgb_tile[3*i+2] = tile[i]

        surf = SDL_CreateRGBSurfaceWithFormatFrom(bytes(rgb_tile), tile_width,
                                                  tile_height, 24, 3*tile_width,
                                                  sdl2.SDL_PIXELFORMAT_RGB24)
        if not surf:
            raise SDL_Error()
        else:
            yield SDL_ConvertSurfaceFormat(surf, format, 0)
            SDL_FreeSurface(surf)


def encode_rgb(iterable: Iterable[int], palette: Sequence[int]) \
        -> Iterable[int]:
    """Consumes an iterable of byte values and generates pairs of bytes
    representing 8 pixels.

    :param iterable: RGB8 grayscale decoded image.
    :param palette: List of colors used to encode iterable.
    :returns: An iterable of encoded data.
    """
    try:
        iterable = iter(iterable)
        while True:
            hi = 0
            lo = 0
            for i in range(8):
                b = next(iterable)
                c = palette.index(b)
                hi |= (c >> 1) << (7 - i)
                lo |= (c & 1) << (7 - i)
            yield hi
            yield lo
    except StopIteration:
        raise StopIteration


def decode_2bit(iterable: Iterable[int], palette: Sequence[Color]) \
        -> Iterable[int]:
    """For every two bytes consumed from the given iterable, generates 8 decoded
    RGB8 colors based on the palette.

    :param iterable: 2-bit grayscale encoded image.
    :param palette: List of colors used to decode the iterable.
    :returns: An iterable of decoded data.
    """
    iterable = iter(iterable)
    #print(palette)
    try:
        while True:
            hi = next(iterable)
            lo = next(iterable)
            for i in range(8):
                c = (lo >> (7-i)) & 1
                c |= ((hi >> (7-i)) & 1) << 1
                color = palette[c]
                yield color
    except StopIteration:
        raise StopIteration()


class RGBTileset():
    """Grayscale RGB8 decoded tileset.

    :param data: Decoded tileset data.
    :param size: Image dimensions in pixels.
    :param tile_size: Tile dimensions in pixels.
    """
    def __init__(self, data, size, tile_size):
        self.size = size
        self.tile_size = tile_size
        self.data = data

    # Must use a string for GBTileset type hint because it's defined later
    @staticmethod
    def from_gb(gbtileset: 'GBTileset', palette: Sequence[int]) \
            -> 'RGBTileset':
        """Decode a 2-bit grayscale tileset to grayscale RGB8 using a palette.

        :param gbtileset: The encoded tileset object.
        :param palette: A list of colors used to decode the image.
        :returns: A decoded RGB8 tileset.
        """
        size = gbtileset.size
        tile_size = gbtileset.tile_size
        width, height = gbtileset.size
        twidth, theight = tile_size
        width_tiles = width // twidth
        height_tiles = height // theight
        encoded_tiles = gbtileset.split_tiles()
        decoded_data = bytearray(width*height)
        for i, et in enumerate(encoded_tiles):
            tx = (i % width_tiles) * twidth
            ty = (i // width_tiles) * theight
            decoded_tile = bytes(decode_2bit(et, palette))
            for y in range(theight):
                row = decoded_tile[y*twidth:(y+1)*twidth]
                decoded_data[(ty+y)*width+tx:(ty+y)*width+tx+twidth] = row
        return RGBTileset(decoded_data, gbtileset.size, gbtileset.tile_size)

    def to_gb(self, palette: Sequence[int]) -> 'GBTileset':
        return GBTileset.from_rgb(self, palette)

    def split_tiles(self) -> Sequence[Sequence[int]]:
        """In the encoded data, tiles are stored contiguously; decoded, they're
        stored in a grid, like you might expect a tileset image to look.

        :returns: A list of tiles.
        """
        width, height = self.size
        twidth, theight = self.tile_size
        width_tiles = width // twidth
        height_tiles = height // theight
        for i in range(width_tiles*height_tiles):
            tile = bytearray(twidth*theight)
            tx = (i % width_tiles) * twidth
            ty = (i // width_tiles) * theight
            for y in range(ty, ty+theight):
                row = self.data[y*width+tx:y*width+tx+twidth]
                tile[twidth*(y-ty):twidth*(y-ty)+twidth] = row
            yield tile


class GBTileset():
    """2-bit encoded tileset.

    :param data: Encoded tileset data.
    :param size: Image dimensions in pixels.
    :param tile_size: Tile dimensions in pixels.
    """
    def __init__(self, data, size, tile_size):
        self.size = size
        self.tile_size = tile_size
        self.data = data

    def split_tiles(self):
        """An 8x8 tile is 16 bytes long; split the encoded block of data into
        chunks based on the size of a tile.
        """
        twidth, theight = self.tile_size
        tsize_bytes = (twidth // 8) * theight * 2
        return (self.data[i:i+tsize_bytes] for i in range(0, len(self.data),
                                                          tsize_bytes))

    @staticmethod
    def from_rgb(rgbtileset: RGBTileset, palette: Sequence[int]) \
            -> 'GBTileset':
        """Encode a tileset using the colors defined by a palette

        :param rgbtileset: Source tileset.
        :param palette: List of colors used to encode the image.
        :returns: An encoded tileset object.
        """
        width, height = rgbtileset.size
        twidth, theight = rgbtileset.tile_size
        width_tiles = width // twidth
        height_tiles = height // theight
        tsize_bytes = (twidth // 8) * theight * 2
        encoded_data = bytearray(width_tiles * height_tiles * tsize_bytes)
        for i, dt in enumerate(rgbtileset.split_tiles()):
            encoded_data[i*tsize_bytes:(i+1)*tsize_bytes] = \
                    bytes(encode_rgb(dt, palette))
        return GBTileset(encoded_data, rgbtileset.size, rgbtileset.tile_size)

    def to_rgb(self, palette: Sequence[int]) -> RGBTileset:
        return RGBTileset.from_gb(self, palette)

if __name__ == '__main__':
    from PIL import Image

    palette = [0xff, 0x55, 0xaa, 0x00]

    img_size = (128, 48)
    tile_size = (8, 8)

    with open('gym.2bpp', 'rb') as f:
        encoded_data_correct = f.read()
    img = Image.open('gym.png')
    assert img.size == img_size
    decoded_data_correct = img.tobytes()

    rgbtileset = RGBTileset(decoded_data_correct, img_size, tile_size)
    gbtileset = GBTileset.from_rgb(rgbtileset, palette)
    for i, (b1, b2) in enumerate(zip(gbtileset.data, encoded_data_correct)):
        print(i, b1, b2)
        assert b1 == b2

    gbtileset = GBTileset(encoded_data_correct, img_size, tile_size)
    rgbtileset = RGBTileset.from_gb(gbtileset, palette)
    for i, (b1, b2) in enumerate(zip(rgbtileset.data, decoded_data_correct)):
        print(i, b1, b2)
        assert b1 == b2

    print('TEST OK')
