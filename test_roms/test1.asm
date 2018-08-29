
;;
;; Test 1
;;
;; Test background display.
;;

define(LCDC,    0xff40)
define(STAT,    0xff41)
define(SCY,     0xff42)
define(SCX,     0xff43)
define(LY,      0xff44)
define(LYC,     0xff45)
define(BGP,     0xff47)
define(OBP0,    0xff48)
define(OBP1,    0xff49)
define(WY,      0xff4a)
define(WX,      0xff4b)

define(VRAM ,0x8000)

    include "header.asm"

    org 0x0150
;;
;; Entry point
;;

;; initialize graphics registers

    ;; LCDC:
    ;; - disable display
    ;; - select BG tiledata at 0x8000
    ;; - disable window display
    ;; - disable sprite display
    ;; - disable BG display
    ld hl, LCDC
    ld (hl), 0x10

    ;; disable STAT interrupts
    inc hl
    ld (hl), 0x00
    
    ;; SCX, SCY = 0
    inc hl
    ld (hl), 0x00
    inc hl
    ld (hl), 0x00

    ;; LYC = 0
    inc hl
    inc hl
    ld (hl), 0x00

    ;; BGP = black (3), dark gray, light gray, white (0)
    inc hl
    ld (hl), 0xe4

    ;; OBPx = 0 (transparent)
    inc hl
    ld (hl), 0x00
    inc hl
    ld (hl), 0x00

    ;; WY, WX = 0
    inc hl
    ld (hl), 0x00
    inc hl
    ld (hl), 0x00


;; copy tileset into VRAM (0x8000-0x8fff)
    ld hl, 0x8000
    ld bc, tileset
loop0:
    ld a, h
    cp 0x90
    jr z, endloop0
    ld a, (bc)
    ld (hl), a
    inc bc
    inc hl
    ld a, (bc)
    ld (hl), a
    inc bc
    inc hl
    jr loop0
endloop0:
    ;halt

;; copy tilemap into VRAM (0x9800-0x9bff)
    ld hl, 0x9800
    ld bc, tilemap
loop1:
    ld a, h
    cp 0x9c
    jr z, endloop1
    ld a, (bc)
    ld (hl), a
    inc bc
    inc hl
    ld a, (bc)
    ld (hl), a
    inc bc
    inc hl
    jr loop1
endloop1:

    ;; enable BG display
    ld hl, LCDC
    set 0, (hl)
    ;; enable display
    set 7, (hl)

    ld bc, 0x0000
loop2:
    inc bc
    ld a, b
    cp 0x01
    jr z, endloop2
    nop
    nop
    nop
    nop
    jr loop2
endloop2:
    ld b, 0
    ld hl, BGP
    ld (hl), 0xe4
    ld hl, SCX
    inc (hl)
    ld a, (hl)
    ; if a == 6*16 then a = 0
    cp 6*16
    jr nz, else2
    ld a, 0
else2:
    ld (hl), a
    jr loop2
    halt


tileset:
    incbin "tileset1.bin"

tilemap:
    incbin "tilemap1.bin"
