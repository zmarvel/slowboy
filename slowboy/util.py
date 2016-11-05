

def uint8toBCD(uint8):
    """Convert an 8-bit unsigned integer to binary-coded decimal."""

    d1 = uint8 // 10
    d0 = uint8 % 10

    return (d1 << 4) | d0
