0x76    0111 0110   halt
0x00    0000 0000   nop
0x10    0001 0000   stop
0xfb    1111 1011   ei
0xf3    1111 0011   di

B:    000
C:    001
D:    010
E:    011
H:    100
L:    101
(HL): 110
A:    111

01dd dsss

0x40    0100 0000   ld B, B                 ✓   0100 0xxx
0x41    0100 0001   ld B, C
0x42    0100 0010   ld B, D
0x43    0100 0011   ld B, E
0x44    0100 0100   ld B, H
0x45    0100 0101   ld B, L
0x46    0100 0110   ld B, (HL)
0x47    0100 0111   ld B, A

0x48    0100 1000   ld C, B                     0100 1xxx
0x49    0100 1001   ld C, C
0x4a    0100 1010   ld C, D
0x4b    0100 1011   ld C, E
0x4c    0100 1100   ld C, H
0x4d    0100 1101   ld C, L
0x4e    0100 1110   ld C, (HL)
0x4f    0100 1111   ld C, A

0x50    0101 0000   ld D, B                     0101 0xxx
0x51    0101 0001   ld D, C
0x52    0101 0010   ld D, D
0x53    0101 0011   ld D, E
0x54    0101 0100   ld D, H
0x55    0101 0101   ld D, L
0x56    0101 0110   ld D, (HL)
0x57    0101 0111   ld D, A

0x58    0101 1000   ld E, B                     0101 1xxx
0x59    0101 1001   ld E, C
0x5a    0101 1010   ld E, D
0x5b    0101 1011   ld E, E
0x5c    0101 1100   ld E, H
0x5d    0101 1101   ld E, L
0x5e    0101 1110   ld E, (HL)
0x5f    0101 1111   ld E, A

0x60    0110 0000   ld H, B                     0110 0xxx
0x61    0110 0001   ld H, C
0x62    0110 0010   ld H, D
0x63    0110 0011   ld H, E
0x64    0110 0100   ld H, H
0x65    0110 0101   ld H, L
0x66    0110 0110   ld H, (HL)
0x67    0110 0111   ld H, A

0x68    0110 1000   ld L, B
0x69    0110 1001   ld L, C
0x6a    0110 1010   ld L, D
0x6b    0110 1011   ld L, E
0x6c    0110 1100   ld L, H
0x6d    0110 1101   ld L, L
0x6e    0110 1110   ld L, (HL)
0x6f    0110 1111   ld L, A

0x70    0111 0000   ld (HL), B
0x71    0111 0001   ld (HL), C
0x72    0111 0010   ld (HL), D
0x73    0111 0011   ld (HL), E
0x74    0111 0100   ld (HL), H
0x75    0111 0101   ld (HL), L
0x77    0111 0111   ld (HL), A

0x78    0111 1000   ld A, B
0x79    0111 1001   ld A, C
0x7a    0111 1010   ld A, D
0x7b    0111 1011   ld A, E
0x7c    0111 1100   ld A, H
0x7d    0111 1101   ld A, L
0x7e    0111 1110   ld A, (HL)
0x7f    0111 1111   ld A, A

0x01    0000 0001   ld BC, nn 00xx 0001     ✓
0x11    0001 0001   ld DE, nn
0x21    0010 0001   ld HL, nn
0x31    0011 0001   ld SP, nn

0x02    0000 0010   ld (BC), A 00xx 0010    ✓
0x12    0001 0010   ld (DE), A
0x22    0010 0010   ldi (HL), A             ✓
0x32    0011 0010   ldd (HL), A

0x06    0000 0110   ld B, n     00xx x110   ✓
0x0e    0000 1110   ld C, n
0x16    0001 0110   ld D, n
0x1e    0001 1110   ld E, n
0x26    0010 0110   ld H, n
0x2e    0001 1110   ld L, n
0x36    0011 0110   ld (HL), n
0x3e    0001 1110   ld A, n

0x08    0000 1000   ld (nn), SP             ✓

0x0a    0000 1010   ld A, (BC)  00xx 1010   ✓
0x1a    0001 1010   ld A, (DE)
0x2a    0010 1010   ldi A, (HL)             ✓
0x3a    0011 1010   ldd A, (HL)

0xe0    1110 0000   ldh (n), A              ✓
0xf0    1111 0000   ldh A, (n)

0xea    1110 1010   ld (nn), A              ✓
0xfa    1111 1010   ld A, (nn)

0xf8    1111 1000   ldhl SP, n              ✓
0xf9    1111 1001   ld SP, HL

0x04    0000 0100   inc B       00xx x100   ✓
0x0c    0000 1100   inc C
0x14    0001 0100   inc D
0x1c    0001 1100   inc E
0x24    0010 0100   inc H
0x2c    0010 1100   inc L
0x34    0011 0100   inc (HL)
0x3c    0011 1100   inc A

0x03    0000 0011   inc BC      00xx 0011   ✓
0x13    0001 0011   inc DE
0x23    0010 0011   inc HL
0x33    0011 0011   inc SP
0x0b    0000 1011   dec BC      00xx 1011   ✓
0x1b    0001 1011   dec DE
0x2b    0010 1011   dec HL
0x3b    0011 1011   dec SP

0x05    0000 0101   dec B       00xx x101   ✓
0x0d    0000 1101   dec C
0x15    0001 0101   dec D
0x1d    0001 1101   dec E
0x25    0010 0101   dec H
0x2d    0010 1101   dec L
0x35    0011 0101   dec (HL)
0x3d    0011 1101   dec A

0x07    0000 0111   rlc A       000x 0111   ✓
0x17    0001 0111   rl A
0x27    0010 0111   daa
0x37    0011 0111   scf

0x80    1000 0000   add A, B    1000 0xxx   ✓
0x81    1000 0001   add A, C
0x82    1000 0010   add A, D
0x83    1000 0011   add A, E
0x84    1000 0100   add A, H
0x85    1000 0101   add A, L
0x87    1000 0111   add A, A
0x88    1000 1000   adc A, B    1000 1xxx   ✓
0x89    1000 1001   adc A, C
0x8a    1000 1010   adc A, D
0x8b    1000 1011   adc A, E
0x8c    1000 1100   adc A, H
0x8d    1000 1101   adc A, L
0x8f    1000 1111   adc A, A

0xe8    1110 1000   add SP, d   1110 1000   ✓

0x90    1001 0000   sub A, B    1001 0xxx   ✓
0x91    1001 0001   sub A, C
0x92    1001 0010   sub A, D
0x93    1001 0011   sub A, E
0x94    1001 0100   sub A, H
0x95    1001 0101   sub A, L
0x97    1001 0111   sub A, A

0x98    1001 1000   sbc A, B    1001 1xxx   ✓
0x99    1001 1001   sbc A, C
0x9a    1001 1010   sbc A, D
0x9b    1001 1011   sbc A, E
0x9c    1001 1100   sbc A, H
0x9d    1001 1101   sbc A, L
0x9f    1001 1111   sbc A, A

0xa0    1010 0000   and B       1010 0xxx   ✓
0xa1    1010 0001   and C
0xa2    1010 0010   and D
0xa3    1010 0011   and E
0xa4    1010 0100   and H
0xa5    1010 0101   and L
0xa7    1010 0111   and A

0xa8    1010 1000   xor B       1010 1xxx   ✓
0xa9    1010 1001   xor C
0xaa    1010 1010   xor D
0xab    1010 1011   xor E
0xac    1010 1100   xor H
0xad    1010 1101   xor L
0xaf    1010 1111   xor A

0xb0    1011 0000   or B        1011 0xxx   ✓
0xb1    1011 0001   or C
0xb2    1011 0010   or D
0xb3    1011 0011   or E
0xb4    1011 0100   or H
0xb5    1011 0101   or L
0xb7    1011 0111   or A

0xb8    1011 1000   cp B        1011 1xxx   ✓
0xb9    1011 1001   cp C
0xba    1011 1010   cp D
0xbb    1011 1011   cp E
0xbc    1011 1100   cp H
0xbd    1011 1101   cp L
0xbf    1011 1111   cp A

0x86    1000 0110   add A, (HL) 1000 x110   ✓
0x8e    1000 1110   adc A, (HL)
0x96    1001 0110   sub A, (HL) 1101 x110   ✓
0x9e    1001 1110   sbc A, (HL)
0xa6    1010 0110   and (HL)    101x x110   ✓
0xae    1010 1110   xor (HL)
0xb6    1011 0110   or (HL)
0xbe    1011 1110   cp (HL)

                                11xx x1x0
0xc6    1100 0110   add A, n    1100 x110   ✓
0xce    1100 1110   adc A, n
0xd6    1101 0110   sub A, n    1101 x110   ✓
0xde    1101 1110   sbc A, n
0xe6    1110 0110   and n       111x x110   ✓
0xee    1110 1110   xor n
0xf6    1111 0110   or n
0xfe    1111 1110   cp n

0xc1    1100 0001   pop BC      11xx 0001   ✓
0xd1    1101 0001   pop DE
0xe1    1110 0001   pop HL
0xf1    1111 0001   pop AF

0xc5    1100 0101   push BC     11xx 0101   ✓
0xd5    1101 0101   push DE
0xe5    1110 0101   push HL
0xf5    1111 0101   push AF

0x20    0010 0000   jr NZ, n    001x 0000
0x30    0011 0000   jr NC, n 

0xca    1100 1010   jp Z, nn    110x 1010
0xda    1101 1010   jp C, nn
0xc2    1100 0010   jp NZ, nn   110x 0010
0xd2    1101 0010   jp NC, nn
0xe9    1110 1001   jp (HL)     1110 1001
0xc3    1100 0011   jp nn       1100 0011

0xcc    1100 1100   call Z, nn  110x 1100
0xdc    1101 1100   call C, nn
0xc4    1100 0100   call NZ, nn 110x 0100
0xd4    1101 0100   call NC, nn
0xcd    1100 1101   call nn     1100 1101

0xc8    1100 1000   ret Z       110x 1000
0xd8    1101 1000   ret C
0xc0    1100 0000   ret NZ      110x 0000
0xd0    1101 0000   ret NC
0xc9    1100 1001   ret         110x 1001
0xd9    1101 1001   reti

0xc7    1100 0111   rst 0x00    10xx x111
0xcf    1100 1111   rst 0x08
0xd7    1101 0111   rst 0x10
0xdf    1101 1111   rst 0x18
0xe7    1110 0111   rst 0x20
0xef    1110 1111   rst 0x28
0xf7    1111 0111   rst 0x30
0xff    1111 1111   rst 0x38




0xcb    1100 1011   16-BIT OPERATION
