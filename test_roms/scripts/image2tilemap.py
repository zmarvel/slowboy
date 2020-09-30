#!/usr/bin/env python3

from PIL import Image

def rgb_i2bit(iterable):
    """Consumes an iterable of byte values and generates pairs of bytes
    representing 8 pixels.
    """
    try:
        iterable = iter(iterable)
        while True:
            hi = 0
            lo = 0
            for i in range(8):
                c = (next(iterable) >> 6) ^ 0x3
                hi |= (c >> 1) << (7 - i)
                lo |= (c & 1) << (7 - i)
            yield hi
            yield lo
    except StopIteration:
        return


def imageto2bit(img, tile_size):
    """Convert a (grayscale) PIL Image to 2-bit
    """
    #img = Image.open(filename).convert(mode='L')
    width, height = img.size
    twidth, theight = tile_size
    width_tiles = width // twidth
    height_tiles = height // theight
    img_bytes = img.tobytes()
    assert len(img_bytes) == width_tiles*height_tiles*twidth*theight
    tiles = []
    for i in range(width_tiles*height_tiles):
        tile = []
        tx = (i % width_tiles) * twidth
        ty = (i // width_tiles) * twidth
        for j in range(theight):
            y = ty + j
            row = img_bytes[y*width+tx:y*width+tx+twidth]
            tile.extend(row)
        tiles.append(tile)

    encoded = []
    for tile in tiles:
        assert len(tile) == twidth*theight
        encoded.extend(rgb_i2bit(tile))

    return bytes(encoded)


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=(
        'Convert an image to a GameBoy tilemap (2-bit color).'
        ))
    parser.add_argument('in_file', type=str,
                        help=('An image (any format supported by Pillow) to'
                              'be converted'))
    parser.add_argument('out_file', type=str,
                        help='A writable output file.')
    parser.add_argument('--asm', action='store_true',
                        help='Output in Z80 assembly instead of binary data.')

    args = parser.parse_args()
    try:
        img = Image.open(args.in_file).convert('L')
    except IOError:
        parser.print_help()
        sys.exit()

    #tileset = Tileset(img.tobytes(), img.size, (8, 8), encoded=False)
    rgb2_bytes = bytes(imageto2bit(img, (8, 8)))

    if args.asm:
        with open(args.out_file, 'w') as f:
            for i, b in enumerate(rgb2_bytes):
                f.write('db %{:08b}\n'.format(b))
                if i & 0x7 == 0x7:
                    f.write('\n')
    else:
        with open(args.out_file, 'wb') as f:
            f.write(rgb2_bytes)
    print('Wrote output to {}'.format(args.out_file))
