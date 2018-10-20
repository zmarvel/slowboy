
;;
;; Test 1
;;
;; Test foreground display.
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
    ;; - select FG tilemap at 0x9c00
    ;; - select BG tiledata at 0x8000
    ;; - disable window display
    ;; - disable sprite display
    ;; - disable BG display
    ld hl, LCDC
    ld (hl), 0x50

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
tilesetcopyloop:
    ld a, h
    cp 0x90
    jr z, endtilesetcopyloop
    ld a, (bc)
    ld (hl), a
    inc bc
    inc hl
    ld a, (bc)
    ld (hl), a
    inc bc
    inc hl
    jr tilesetcopyloop
endtilesetcopyloop:
    ;halt

;; copy bg tilemap into VRAM (0x9800-0x9bff)
    ld hl, 0x9800
    ld bc, tilemap
bgcopyloop:
    ld a, h
    cp 0x9c
    jr z, endbgcopyloop
    ld a, (bc)
    ld (hl), a
    inc bc
    inc hl
    ld a, (bc)
    ld (hl), a
    inc bc
    inc hl
    jr bgcopyloop
endbgcopyloop:


;; copy fg tilemap into VRAM (0x9c00-0x9ffff)
    ld hl, 0x9c00
    ld bc, tilemap+0x400
fgcopyloop:
    ld a, h
    cp 0xa0
    jr z, endfgcopyloop
    ld a, (bc)
    ld (hl), a
    inc bc
    inc hl
    ld a, (bc)
    ld (hl), a
    inc bc
    inc hl
    jr fgcopyloop
endfgcopyloop:

    ld hl, WX
    ld (hl), 7
    ld hl, WY
    ld (hl), 96

    ;; enable BG display
    ld hl, LCDC
    set 0, (hl)
    ;; enable FG display
    set 5, (hl)
    ;; enable display
    set 7, (hl)


    ld bc, 0x0000
mainloop:
    inc bc
    ld a, b
    cp 0x01
    jr z, endmainloop
    nop
    nop
    nop
    nop
    jr mainloop
endmainloop:
    ld b, 0
    ld hl, SCX
    inc (hl)
    ld a, (hl)
    ; if a == 6*16 then a = 0
    cp 6*16
    jr nz, else_mainloopagain
    ld a, 0
else_mainloopagain:
    ld (hl), a
    jr mainloop
    halt


tileset:
    incbin "tileset2.bin"

tilemap:
    incbin "tilemap2.bin"
