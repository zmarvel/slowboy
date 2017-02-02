#!/usr/bin/env python3
"""Somewhat dirty script to decode the Nintendo logo as found in GameBoy games
to an image. Only depends on Pillow."""

import sys
from PIL import Image

BMP = (
        b'\xCE\xED\x66\x66\xCC\x0D\x00\x0B\x03\x73\x00\x83\x00\x0C\x00\x0D'
        b'\x00\x08\x11\x1F\x88\x89\x00\x0E\xDC\xCC\x6E\xE6\xDD\xDD\xD9\x99'
        b'\xBB\xBB\x67\x63\x6E\x0E\xEC\xCC\xDD\xDC\x99\x9F\xBB\xB9\x33\x3E'
        )
WIDTH = 48
HEIGHT = 8

def main():
    if len(sys.argv) < 2:
        print('USAGE: {} OUTFILE'.format(sys.argv[0]))
        exit(-1)

    def split_nibbles(bmp):
        ns = []
        for b in bmp:
            high = b >> 4
            low = b & 0xf
            ns.append(high)
            ns.append(low)
        return ns

    def bittorgb(b):
        if b == 0:
            return (255, 255, 255)
        else:
            return (0, 0, 0)

    def nibblestorgb(ns, rgb, rgb_width, rgb_height):
        for i, n in enumerate(ns):
            rgb_row = (i % 4) + 4*(i // rgb_width)
            rgb_col = 4*(i // 4) % rgb_width
            idx = rgb_row * rgb_width + rgb_col
            print(i, rgb_row, rgb_col, idx)

            rgb[idx] = bittorgb((n >> 3) & 1)
            rgb[idx+1] = bittorgb((n >> 2) & 1)
            rgb[idx+2] = bittorgb((n >> 1) & 1)
            rgb[idx+3] = bittorgb(n & 1)

    rgb = [None for _ in range(WIDTH * HEIGHT)]
    nibblestorgb(split_nibbles(BMP), rgb, WIDTH, HEIGHT)
   
    print(rgb)

    i = Image.new('RGB', (WIDTH, HEIGHT))
    i.putdata(rgb)
    i.save(sys.argv[1])

if __name__ == '__main__':
    main()
