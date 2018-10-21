
;;
;; Test 1
;;
;; Test background display.
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
    ;; - select BG tiledata at $8000
    ;; - disable window display
    ;; - disable sprite display
    ;; - disable BG display
    ld hl, LCDC
    ld [hl], $10

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
loop0:
    ld a, h
    cp $90
    jr z, endloop0
    ld a, [bc]
    ld [hl], a
    inc bc
    inc hl
    ld a, [bc]
    ld [hl], a
    inc bc
    inc hl
    jr loop0
endloop0:
    ;halt

;; copy tilemap into VRAM ($9800-$9bff)
    ld hl, $9800
    ld bc, tilemap
loop1:
    ld a, h
    cp $9c
    jr z, endloop1
    ld a, [bc]
    ld [hl], a
    inc bc
    inc hl
    ld a, [bc]
    ld [hl], a
    inc bc
    inc hl
    jr loop1
endloop1:

    ;; enable BG display
    ld hl, LCDC
    set 0, [hl]
    ;; enable display
    set 7, [hl]

    ld bc, $0000
loop2:
    inc bc
    ld a, b
    cp $01
    jr z, endloop2
    nop
    nop
    nop
    nop
    jr loop2
endloop2:
    ld b, 0
    ld hl, BGP
    ld [hl], $e4
    ld hl, SCX
    inc [hl]
    ld a, [hl]
    ; if a == 6*16 then a = 0
    cp 6*16
    jr nz, else2
    ld a, 0
else2:
    ld [hl], a
    jr loop2
    halt


tileset:
    incbin "tileset1.bin"

tilemap:
    incbin "tilemap1.bin"
