
# Shift and rotate instructions

According to the GameBoy Programming Manual, the GameBoy CPU supports the
following shift/rotate instructions:

- RLCA
- RLA
- RRCA
- RRA
- RLC
- RL
- RRC
- RR
- SLA
- SRA
- SRL

## Rotate instructions

I decided to write this note because I don't know how all these instructions
differ.

The RL(C)A/RR(C)A forms are the same as RL(C)/RR(C), but they use register A as
an operand.

RLCA sets the new LSb to the old MSb and sets the carry flag to the old MSb.

```
A = 0b10100101
RLCA
A ← 0b01001011, C ← 1
```

Likewise for RRCA.

```
A = 0b10100101
RRCA
A ← 0b11010010, C ← 1
```

RLA sets the new LSb to the old carry flag and sets the carry flag to the old
MSb.

```
A = 0b10100101, C = 0
RLA
A ← 0b01001010, C ← 1

A = 0b10100101, C = 1
RLA
A ← 0b01001011, C ← 1
```

RRA sets the new MSb to the old carry flag and sets the carry flag to the old
LSb.

```
A = 0b10100101, C = 0
RRA
A ← 0b01010010, C ← 1

A = 0b10100101, C = 1
RRA
A ← 0b11010010, C ← 1
```

## Shift instructions

- SLA: arithmetic shift left
- SRA: arithmetic shift right
- SRL: logical shift right

There is no SLL instruction because SLA behaves the same. Wikipedia describes
both[arithmetic-shift] operations[logical-shift] clearly.

[arithmetic-shift]: https://en.wikipedia.org/wiki/Arithmetic_shift
[logical-shift]: https://en.wikipedia.org/wiki/Logical_shift
