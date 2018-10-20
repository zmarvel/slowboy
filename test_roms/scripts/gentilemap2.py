

import string
import sys

TWIDTH = 8
THEIGHT = 8
TSWIDTH = 128
TSHEIGHT = 128
TSWIDTH_TILES = TSWIDTH // TWIDTH
TSHEIGHT_TILES = TSHEIGHT // THEIGHT

SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144
SWIDTH_TILES = SCREEN_WIDTH // TWIDTH
SHEIGHT_TILES = SCREEN_HEIGHT // THEIGHT

BACKGROUND_WIDTH = 256
BACKGROUND_HEIGHT = 256
BGWIDTH_TILES = BACKGROUND_WIDTH // TWIDTH
BGHEIGHT_TILES = BACKGROUND_HEIGHT // THEIGHT


def s8(u):
    return ((u ^ 0xff) + 1) & 0xff

def sub(a, b):
    return (a + s8(b)) & 0xff

def strtotilemap(s, offset, width, left, right, pad):
    # width in tiles
    # left and right are tileid for left and right border
    # only support one case for now
    s = s.lower()
    out = [left]
    col = 1
    for i in range(len(s)):
        if col == width-1:
            out.append(right)
            out.extend([pad for _ in range(BGWIDTH_TILES-width)])
            out.append(left)
            col = 1
        if s[i] == ' ':
            out.append(pad)
        elif s[i] not in string.ascii_lowercase:
            raise ValueError('only ascii letters are supported: {}')
        else:
            out.append(offset + (ord(s[i]) - 97))
        col += 1
    print(len(out))
    if col <= width:
        # pad
        out.extend([pad for _ in range(width-col-1)])
        out.append(right)
        out.extend([pad for _ in range(BGWIDTH_TILES-width)])
    print(len(out))
    print(out)
    return out

TOPLEFT_CORNER = 64+43
TOPRIGHT_CORNER = 64+44
BOTTOMLEFT_CORNER = 64+50
BOTTOMRIGHT_CORNER = 64+49
TOP_EDGE = 64+46
LEFT_EDGE = 64+45
RIGHT_EDGE = 64+47
BOTTOM_EDGE = 64+48
SPACE = 64+51
HEART = 64+6

fname = sys.argv[1]
with open(fname, 'wb+') as f:
    # bg tilemap: 0x9800-0x9bff = 0x400
    f.write(bytes(x % 64 for x in range(0, 0x400)))
    # fg tilemap: 0x0xc00-0x9fff = 0x400
    top_row = bytes([TOPLEFT_CORNER] + [TOP_EDGE for _ in range(18)] \
                    + [TOPRIGHT_CORNER] + [SPACE for _ in range(BGWIDTH_TILES-20)])
    f.write(top_row)
    encoded = strtotilemap("hello world", 64+17, 20, LEFT_EDGE, RIGHT_EDGE, HEART)
    blank_rows = []
    for i in range(3):
        blank_rows.extend([LEFT_EDGE] + [SPACE for _ in range(18)] + [RIGHT_EDGE])
        blank_rows.extend(HEART for _ in range(BGWIDTH_TILES-SWIDTH_TILES))
    bottom_row = [BOTTOMLEFT_CORNER] + [BOTTOM_EDGE for _ in range(18)] \
            + [BOTTOMRIGHT_CORNER]
    bottom_row.extend(HEART for _ in range(BGWIDTH_TILES-SWIDTH_TILES))
    l = 0x400 - len(top_row) - len(encoded) - len(blank_rows) - len(bottom_row)
    f.write(bytes(encoded))
    f.write(bytes(blank_rows))
    f.write(bytes(bottom_row))
    f.write(bytes(0 for _ in range(l)))
