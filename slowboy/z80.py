
from functools import partial

class gb_z80(object):

    def __init__(self):
        self.clk = 0
        self.m = 0
        self.registers = {
            'a': 0, 'f': 0,
            'b': 0, 'c': 0,
            'd': 0, 'e': 0,
            'h': 0, 'l': 0,
            'sp': 0,
            'pc': 0
            }

    def _init_opcodes(self):
        opcodes = { # all opcodes are functions that take the opcode as the first argument
                0x00: partial(self._nop, 0x00),
                0x10: partial(self._stop, 0x10),
                0x76: partial(self._halt, 0x76),
                0xfb: partial(self._ei, 0xfb),
                0xf3: partial(self._di, 0xf3),
                }

        reg8s = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        reg16s = ['BC', 'DE', 'HL', 'SP']

        for i in range(8):
            for j in range(8): # ld reg8, reg8
                # 01dd dsss
                opcode = 0x40 | (i << 3) | j
                opcodes[opcode] = partial(self._ld, opcode)
        
        for i in range(4): # ld reg16, imm16
            opcode = 0x01 | (i << 4)
            opcodes[opcode] = partial(self._ld, opcode)

        opcodes[0x01] = partial(self._ld, 0x01)  # ld (be), a
        opcodes[0x12] = partial(self._ld, 0x12)  # ld (de), a
        opcodes[0x22] = partial(self._ld, 0x22)  # ldi (hl), a
        opcodes[0x32] = partial(self._ld, 0x32)  # ldd (hl), a

        for i in range(8): # ld reg8, imm8
            opcode = 0x06 | i << 3
            opcodes[opcode] = partial(self._ld, opcode)

        opcodes[0x08] = partial(self_.ld, 0x08) # ld (imm16), SP

        for i in range (4): # ld A, (BC)/(DE) ; ldi/ldd A, (HL)
            opcode = 0x0a | (i << 4)
            opcodes[opcode] = partial(self._ld, opcode)
        
        opcodes[0xe0] = partial(self._ld, 0xe0) # ld ($ff00+imm8), A
        opcodes[0xea] = partial(self._ld, 0xea) # ld ($ff00+imm16), A
        opcodes[0xf0] = partial(self._ld, 0xf0) # ld A, ($ff00+imm8)
        opcodes[0xfa] = partial(self._ld, 0xfa) # ld A, ($ff00+imm16)

        opcodes[0xf8] = partial(self._ld, 0xf8) # ld HL, SP+imm8
        opcodes[0xf9] = partial(self._ld, 0xf9) # ld SP, HL        

        for i in range(8): # inc reg8
            opcode = 0x04 | (i << 3)
            opcodes[opcode] = partial(self._inc, opcode)

        for i in range(8): # dec reg8
            opcode = 0x05 | (i << 3)
            opcodes[opcode] = partial(self._dec, opcode)

        for i in range(4): # inc reg16
            opcode = 0x03 | (i << 4)
            opcodes[opcode] = partial(self._inc, opcode)

        for i in range(4): # dec reg16
            opcode = 0x0b | (i << 4)
            opcodes[opcode] = partial(self._dec, opcode)

        opcode[0x07] = partial(self._rlc, 0x07)
        opcode[0x17] = partial(self._rl, 0x17)
        opcode[0x27] = partial(self._daa, 0x27)
        opcode[0x37] = partial(self._scf, 0x37)

        for i in range(8): # add reg8, reg8
            opcode = 0x80 | i
            opcodes[opcode] = partial(self._add, opcode)
            
        for i in range(8): # adc reg8, reg8
            opcode = 0x88 | i
            opcodes[opcode] = partial(self._adc, opcode)

        opcodes[0xe8] = partial(self._add, opcde) # add SP, imm8 (signed)

        for i in range(8): # sub A, reg8
            opcode = 0x90 | i
            opcodes[opcode] = partial(self._sub, opcode)

        for i in range(8): # sbc A, reg8
            opcode = 0x98 | i
            opcodes[opcode] = partial(self._sbc, opcode)
            
        for i in range(8): # and reg8
            opcode = 0xa0 | i
            opcodes[opcode] = partial(self._and, opcode)

        for i in range(8): # xor reg8
            opcode = 0xa8 | i
            opcodes[opcode] = partial(self._xor, opcode)

        for i in range(8): # or reg8
            opcode = 0xb0 | i
            opcodes[opcode] = partial(self._or, opcode)

        for i in range(8): # cp reg8
            opcode = 0xb8 | i
            opcodes[opcode] = partial(self._cp, opcode)

        opcode = 0xc6 # add A, imm8
        opcodes[opcode] = partial(self._add, opcode)
        opcode = 0xce # adc A, imm8
        opcodes[opcode] = partial(self._adc, opcode)
        opcode = 0xd6 # sub A, imm8
        opcodes[opcode] = partial(self._sub, opcode)
        opcode = 0xde # sbc A, imm8
        opcodes[opcode] = partial(self._sbc, opcode)
        opcode = 0xe6 # and imm8
        opcodes[opcode] = partial(self._and, opcode)
        opcode = 0xee # xor imm8
        opcodes[opcode] = partial(self._xor, opcode)
        opcode = 0xf6 # or imm8
        opcodes[opcode] = partial(self._or, opcode)
        opcode = 0xfe # cp imm8
        opcodes[opcode] = partial(self._cp, opcode)

        for i in range(4): # push reg16
            opcode = 0xc5 | (i << 4)
            opcodes[opcode] = partial(self._push, opcode)

        for i in range(4): # pop reg16
            opcode = 0xc1 | (i << 4)
            opcodes[opcode] = partial(self._pop, opcode)

        opcode = 0x20 # jr nz, imm8
        opcodes[opcode] = partial(self._jr, opcode)
        opcode = 0x30 # jr nc, imm8
        opcodes[opcode] = partial(self._jr, opcode)
        
        opcode = 0xca # jp z, imm16
        opcodes[opcode] = partial(self._jp, opcode)
        opcode = 0xda # jp c, imm16
        opcodes[opcode] = partial(self._jr, opcode)
        opcode = 0xc2 # jp nz, imm16
        opcodes[opcode] = partial(self._jr, opcode)
        opcode = 0xd2 # jp nc, imm16
        opcodes[opcode] = partial(self._jr, opcode)
        opcode = 0xe9 # jp (hl)
        opcodes[opcode] = partial(self._jr, opcode)
        opcode = 0xc3 # jp imm16
        opcodes[opcode] = partial(self._jr, opcode)

        opcode = 0xcc # call z, imm16
        opcodes[opcode] = partial(self._call, opcode)
        opcode = 0xdc # call c, imm16
        opcodes[opcode] = partial(self._call, opcode)
        opcode = 0xc4 # call nz, imm16
        opcodes[opcode] = partial(self._call, opcode)
        opcode = 0xd4 # call nc, imm16
        opcodes[opcode] = partial(self._call, opcode)
        opcode = 0xcd # call imm16
        opcodes[opcode] = partial(self._call, opcode)

        opcode = 0xc8 # ret z
        opcodes[opcode] = partial(self._ret, opcode)
        opcode = 0xd8 # ret c
        opcodes[opcode] = partial(self._ret, opcode)
        opcode = 0xc0 # ret nz
        opcodes[opcode] = partial(self._ret, opcode)
        opcode = 0xd0 # ret nc
        opcodes[opcode] = partial(self._ret, opcode)
        opcode = 0xc9 # ret
        opcodes[opcode] = partial(self._ret, opcode)
        opcode = 0xd9 # ret i
        opcodes[opcode] = partial(self._ret, opcode)

        opcode = 0xc7
        opcodes[opcode] = partial(self._rst, opcode)
        opcode = 0xcf
        opcodes[opcode] = partial(self._rst, opcode)
        opcode = 0xd7
        opcodes[opcode] = partial(self._rst, opcode)
        opcode = 0xdf
        opcodes[opcode] = partial(self._rst, opcode)
        opcode = 0xe7
        opcodes[opcode] = partial(self._rst, opcode)
        opcode = 0xef
        opcodes[opcode] = partial(self._rst, opcode)
        opcode = 0xf7
        opcodes[opcode] = partial(self._rst, opcode)
        opcode = 0xff
        opcodes[opcode] = partial(self._rst, opcode)




    def _increment_pc(self):
        registers['pc'] += 1

    def _advance(self):
        byte = self._read_memory(registers['pc'])
        self.increment_pc()
        return byte
    
    def tick(self):
        op = self._advance()
        opcodes[op]()

    def ld(

    def lookup_opcode(self, opcode):
        hn = opcode >> 4
        ln = opcode & 0xf
        if opcode == 0x00:
            return self._nop
        elif opcode == 0x10:
            return self._stop
        elif opcode == 0x76:
            return self._halt
        elif opcode == 0xcf:
            # di (disable interrupts)
            return self._di
        elif opcode == 0xfb:
            # enable interrupts
            return self._ei
        elif hn >> 2 == 0x1:
            # 01xx xxxx : ld into 8-bit reg
            src_registers = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
            dest_registers = src_registers
            src_idx = opcode & 0x7
            dest_idx = (opcode >> 3) & 0x7
            return self._ld # ld src_registers[src_idx], dest_idx[dest_idx]
        elif opcode & 0xcf == 0x01:
            # 00xx 0001 : ld 16-bit imm into reg
            dest_registers = ['BC', 'DE', 'HL', 'SP']
            dest_idx = hn & 0x3
            return self._ld  # ld dest_registers[dest_idx], imm16
        elif opcode & 0xef == 0x02:
            # 000x 0010 : ld value at 16-bit addr, reg a
            dest_addrs = ['(BC)', '(DE)']
            dest_idx = hn & 0x1
            return self._ld # ld dest_addrs[dest_idx], a
        elif opcode & 0xef == 0x22:
            # 001x 0010 : ld (HL), reg a then increment/decrement HL
            if hn & 0x1 == 1:
                return self._ldi
            else:
                return self._ldd
        elif opcode & 0xc7 == 0x06:
            # 00xx x110 : ld reg8, imm8
            dest_registers = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
            dest_idx = (opcode >> 3) & 0x7
            return self._ld # ld dest_registers[dest_idx], imm8
        elif opcode == 0x08:
            # 0000 1000 : ld SP into value at immediate address
            return self._ld # ld (imm16), SP
        elif opcode & 0xcf == 0x0a:
            # 00xx 1010 : ld value at addr in a reg into reg A
            if hn >> 1 == 0: # 000x 1010
                dest_addrs = ['(BC)', '(DE)']
                dest_idx = hn & 0x1
                return self._ld
            elif hn & 0x1 == 0:
                return self._ldi # ldi a, (hl)
            else:
                return self._ldd # ldd a, (hl)
        elif opcode & 0xef == 0xe0:
            # 111x 0000
            if hn & 0x1 == 0: # ldh (imm8), a -> ld ($FF00+imm8), a
                return self._ldh
            else: # ldh a, (imm8) -> ld a, ($FF00+imm8)
                return self._ldh
        elif opcode & 0xef == 0xea:
            # 111x 1010
            if hn & 1: # ld (imm16), a
                return self._ld
            else: # ld a, (imm16)
                return self._ld
        elif opcode & 0xfe == 0xf8:
            # 1111 111x
            if ln & 0x1 == 1: # ld SP, HL
                return self._ld
            else: # ldhl SP, imm8 -> ld HL, SP+imm8
                return self._ld
        elif opcode & 0xc7 == 0x04:
            # 00xx x100: inc regs[reg_idx] (8-bit)
            regs = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
            reg_idx = (opcode >> 3) & 0x7
            return self._inc
        elif opcode & 0xc7 == 0x05:
            # 00xx x101 : dec regs[reg_idx] (8-bit)
            regs = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
            reg_idx = (opcode >> 3) & 0x7
            return self._dec
        elif opcode & 0xcf == 0x03:
            # 00xx 0011 : inc regs[reg_idx] (16-bit)
            regs = ['BC', 'DE', 'HL', 'SP']
            reg_idx = hn & 0x3
            return self._inc
        elif opcode & 0xcf == 0x0b:
            # 00xx 1011 : dec regs[reg_dx] (16-bit)
            regs = ['BC', 'DE', 'HL', 'SP']
            reg_idx = hn & 0x3
            return self._dec
        elif opcode & 0xef == 0x07:
            # 000x 0111 : rl/rlc a
            if hn & 0x1 == 1:
                return self._rl
            else:
                return self._rlc
        elif opcode == 0x27:
            return self._daa
        elif opcode == 0x37:
            return self._scf
        elif opcode & 0xf0 == 0x80:
            # 1000 xxxx : add/adc A, reg8
            src_regs = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
            src_idx = ln & 0x3
            if ln >> 3 == 1:
                return self._adc
            else:
                return self._add
        elif opcode == 0xe8:
            # 1110 1000 : add SP, imm8 (signed)
            return self._add
        elif opcode & 0xf8 == 0x90:
            # 1001 1xxx : sub/subc A, reg8
            src_regs = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
            src_idx = ln & 0x3
            if ln >> 3 == 1:
                return self._sbc
            else:
                return self._sub
        elif opcode & 0xf8 == 0xa8:
            # 1010 1xxx : xor reg8 (i.e. reg8 ^ A)
            src_regs = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
            src_idx = ln & 0x3
            return self._xor
        elif opcode & 0xf8 == 0xb0:
            # 1011 0xxx : or reg8 (i.e. reg8 | A)
            src_regs = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
            src_idx = ln & 0x3
            return self._or
        elif opcode & 0xf8 == 0xb8:
            # 1011 1xxx : cp reg8 (i.e. reg8 == A)
            src_regs = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
            src_idx = ln & 0x3
            return self._cp
        elif opcode & 0xf7 == 0x86:
            # 1000 x110 : add/c A, (HL)
            if hn >> 3 == 1:
                return self._adc
            else:
                return self._add
        elif opcode & 0xf7 == 0xd6:
            if hn >> 3 == 1:
                return self._sbc
            else:
                return self._sub
        elif opcode & 0xe7 == 0xa6:
            # 101x x110 : and/xor/or/cp (HL)
            instructions = [self._and, self._xor, self._or, self_cp]
            instruction_idx = (opcode >> 3) & 0x3
            return instructions[instructions_idx]
        elif opcode & 0xf7 == 0xc6:
            # 1100 x110 : add/adc A, imm8
            if ln >> 3 == 1:
                return self._adc
            else:
                return self._add
        elif opcode & 0xf7 == 0xd6:
            # 1101 x110 : sub/subc A, imm8
            if ln >> 3 == 1:
                return self._sbc
            else:
                return self._sub
        elif opcode & 0xe7 == 0xe6:
            # 111x x110 : and/xor/or/cp imm8 (i.e. and/xor/or/cp imm8, A)
            instructions = [self._and, self._xor, self._or, self_cp]
            instruction_idx = (opcode >> 3) & 0x3
            return instructions[instruction_idx]
        elif opcode & 0xcf == 0xc1:
            # 11xx 0001 : pop reg16
            dest_regs = ['BC', 'DE', 'HL', 'AF']
            dest_idx = hn & 0x2
            return self._pop
        elif opcode & 0xcf == 0xc5:
            # 11xx 0101 : push reg16
            src_egs = ['BC', 'DE', 'HL', 'AF']
            src_idx = hn & 0x2
            return self._pop
        elif 
        




            








        


            
            
   def read_register(self, reg: str) -> int:
        if len(reg) == 1:
            return (registers[reg[0]] << 8) | registers[reg[1]]
        return registers[reg]

    def write_register(self, reg: str, v: int):
        if len(reg) == 1
        if lo:
            registers[reg[0]] = v >> 8
            registers[reg[1]] = v & 0x0f
        registers[reg] = v
    
    def _set_zero_flag(self):
        registers['f'] |= 0x80
    
    def _reset_zero_flag(self):
        registers['f'] &= 0x7f

    def _set_carry_flag(self):
        registers['f'] |= 0x10

    def _reset_carry_flag(self):
        registers['f'] &= 0xef

    def _set_addsub_flag(self):
        registers['f'] |= 0x40

    def _reset_addsub_flag(self):
        registers['f'] &= 0xbf

    def _set_halfcarry_flag(self):
        registers['f'] |= 0x20

    def _reset_halfcarry_flag(self):
        registers['f'] &= 0xdf
    

