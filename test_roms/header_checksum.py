

#title
hdr = [ord(c) for c in "SLOWBOY\0"]

# manuf code, new licensee code
hdr += [0, 0, 0, 0, 0]

# sgb flag
hdr += [0]

# cart type
hdr += [0]

# ROM size
hdr += [0]

# RAM size
hdr += [0]

# dest code
hdr += [1]

# old licensee code
hdr += [0x33]

# mask rom version
hdr += [0]

def not8(x):
    return x ^ 0xff

def sub(x, y):
    # x - y
    return (x + not8(y) + 1) & 0xff

chksum = 0
for x in hdr:
    chksum = sub(chksum, sub(x, 1))

print(chksum)

#chksum = 0
#for x in hdr:
#    chksum = chksum - x - 1
#
#print(chksum & 0xff)
