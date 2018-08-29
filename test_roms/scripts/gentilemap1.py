

import sys

fname = sys.argv[1]
with open(fname, 'wb') as f:
    f.write(bytes(x % 64 for x in range(0, 0x8000)))
