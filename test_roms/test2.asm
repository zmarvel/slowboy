
;;
;; Test 1
;;
;; Test foreground display.
;;

define(LCDC,    $ff40)
define(STAT,    $ff41)
define(SCY,     $ff42)
define(SCX,     $ff43)
define(LY,      $ff44)
define(LYC,     $ff45)
define(BGP,     $ff47)
define(OBP0,    $ff48)
define(OBP1,    $ff49)
define(WY,      $ff4a)
define(WX,      $ff4b)

define(VRAM ,$8000)

    include "header.asm"

SECTION "EntryPoint",ROM0[$150]
;;
;; Entry point
;;

;; initialize graphics registers

    ;; LCDC:
    ;; - disable display
    ;; - select FG tilemap at $9c00
    ;; - select BG tiledata at $8000
    ;; - disable window display
    ;; - disable sprite display
    ;; - disable BG display
    ld hl, LCDC
    ld [hl], $50

    ;; disable STAT interrupts
    inc hl
    ld [hl], $00
    
    ;; SCX, SCY = 0
    inc hl
    ld [hl], $00
    inc hl
    ld [hl], $00

    ;; LYC = 0
    inc hl
    inc hl
    ld [hl], $00

    ;; BGP = black (3), dark gray, light gray, white (0)
    inc hl
    inc hl
    ld [hl], $e4

    ;; OBPx = 0 (transparent)
    inc hl
    ld [hl], $00
    inc hl
    ld [hl], $00

    ;; WY, WX = 0
    inc hl
    ld [hl], $00
    inc hl
    ld [hl], $00


;; copy tileset into VRAM ($8000-$8fff)
    ld hl, $8000
    ld bc, tileset
tilesetcopyloop:
    ld a, h
    cp $90
    jr z, endtilesetcopyloop
    ld a, [bc]
    ld [hl], a
    inc bc
    inc hl
    ld a, [bc]
    ld [hl], a
    inc bc
    inc hl
    jr tilesetcopyloop
endtilesetcopyloop:
    ;halt

;; copy bg tilemap into VRAM ($9800-$9bff)
    ld hl, $9800
    ld bc, tilemap
bgcopyloop:
    ld a, h
    cp $9c
    jr z, endbgcopyloop
    ld a, [bc]
    ld [hl], a
    inc bc
    inc hl
    ld a, [bc]
    ld [hl], a
    inc bc
    inc hl
    jr bgcopyloop
endbgcopyloop:


;; copy fg tilemap into VRAM ($9c00-$9ffff)
    ld hl, $9c00
    ld bc, tilemap+$400
fgcopyloop:
    ld a, h
    cp $a0
    jr z, endfgcopyloop
    ld a, [bc]
    ld [hl], a
    inc bc
    inc hl
    ld a, [bc]
    ld [hl], a
    inc bc
    inc hl
    jr fgcopyloop
endfgcopyloop:

    ld hl, WX
    ld [hl], 7
    ld hl, WY
    ld [hl], 96

    ;; enable BG display
    ld hl, LCDC
    set 0, [hl]
    ;; enable FG display
    set 5, [hl]
    ;; enable display
    set 7, [hl]


    ld bc, $0000
mainloop:
    inc bc
    ld a, b
    cp $01
    jr z, endmainloop
    nop
    nop
    nop
    nop
    jr mainloop
endmainloop:
    ld b, 0
    ld hl, SCX
    inc [hl]
    ld a, [hl]
    ; if a == 6*16 then a = 0
    cp 6*16
    jr nz, else_mainloopagain
    ld a, 0
else_mainloopagain:
    ld [hl], a
    jr mainloop
    halt


tileset:
    incbin "tileset2.bin"

tilemap:
    incbin "tilemap2.bin"
