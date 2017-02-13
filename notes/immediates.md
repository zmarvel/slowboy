
0x36    0011 0110   ld (hl), imm8
0x08    0000 1000   ld (imm16), sp

0x06    0000 0110   ld b, imm8
0x0e    0000 1110   ld c, imm8
0x16    0001 0110   ld d, imm8
0x1e    0001 1110   ld e, imm8
0x26    0010 0110   ld h, imm8
0x2e    0010 1110   ld l, imm8
0x3e    0011 1110   ld a, imm8

00xx x110

0xc6    1100 0110   add a, imm8
0xce    1100 1110   adc a, imm8
0xd6    1101 0110   sub imm8
0xde    1101 1110   sbc imm8
0xe6    1110 0110   and imm8
0xee    1110 1110   xor imm8
0xfe    1111 1110   cp imm8
0xf6    1111 0110   or imm8

11xx x110

0x18    0001 1000   jr imm8

0001 1000

0x20    0010 0000   jr nz, imm8
0x28    0010 1000   jr z, imm8
0x30    0011 0000   jr nc, imm8
0x38    0011 1000   jr c, imm8

001x x000

0x01    0000 0001   ld bc, imm16
0x11    0001 0001   ld de, imm16
0x21    0010 0001   ld hl, imm16
0x31    0011 0001   ld sp, imm16

00xx 0001

0xc3    1100 0011   jp imm16

1100 0011

0xc2    1100 0010   jp nz, imm16
0xca    1100 1010   jp z, imm16
0xd2    1101 0010   jp nc, imm16
0xda    1101 1010   jp c, imm16

110x x010

0xcd    1100 1101   call imm16

1100 1101

0xcc    1100 1100   call z, imm16
0xc4    1100 0100   call nz, imm16
0xdc    1101 1100   call c, imm16
0xd4    1110 0100   call nc, imm16

110x x100





0xe8    1110 1000   add sp, imm8
0xf8    1111 1000   ld hl, sp+imm8


0xe0    1110 0000   ldh (imm8), a
0xf0    1111 0000   ldh a, (imm8)
0xea    1110 1010   ld (imm16), a
0xfa    1111 1010   ld a, (imm16)

