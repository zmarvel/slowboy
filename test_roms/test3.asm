
;;
;; Test 1
;;
;; Test sprite display.
;;

define(LCDC,    $ff40)
define(STAT,    $ff41)
define(SCY,     $ff42)
define(SCX,     $ff43)
define(LY,      $ff44)
define(LYC,     $ff45)
define(DMA,     $ff46)
define(BGP,     $ff47)
define(OBP0,    $ff48)
define(OBP1,    $ff49)
define(WY,      $ff4a)
define(WX,      $ff4b)

define(VRAM,    $8000)
define(HRAM,    $ff80)


    include "header.asm"

SECTION "EntryPoint",ROM0[$150]
    jp begin   ; 3 B

;; -----------------------------------------------------------------------------
; $200
SECTION "SpriteTable",ROM0[$200]
spritetab:
sprite0:
    ;; Y=8
    db 24
    ;; X=16
    db 24
    ;; tile 68 (star)
    db 68
    ;; attributes:
    ;; - above BG
    ;; - not vertically mirrored
    ;; - not horizontally mirrored
    db 0

sprite1:
    ;; Y=8
    db 24
    ;; X=24
    db 32
    ;; tile 68 (star)
    db 68
    ;; attributes:
    ;; - above BG
    ;; - not vertically mirrored
    ;; - not horizontally mirrored
    db 0

sprite2:
    ;; Y=16
    db 32
    ;; X=16
    db 24
    ;; tile 68 (star)
    db 68
    ;; attributes:
    ;; - above BG
    ;; - not vertically mirrored
    ;; - not horizontally mirrored
    db 0

sprite3:
    ;; Y=16
    db 32
    ;; X=24
    db 32
    ;; tile 68 (star)
    db 68
    ;; attributes:
    ;; - above BG
    ;; - not vertically mirrored
    ;; - not horizontally mirrored
    db 0


    ds 36*4

endspritetab:


;;
;; Entry point
;;

begin:

;; -----------------------------------------------------------------------------
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
    ;halt

    ;; OBPx = 0 (transparent)
    inc hl
    ld [hl], $e4
    inc hl
    ld [hl], $00

    ;; WY, WX = 0
    inc hl
    ld [hl], $00
    inc hl
    ld [hl], $00

;; -----------------------------------------------------------------------------
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

;; -----------------------------------------------------------------------------
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


;; -----------------------------------------------------------------------------
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


;; -----------------------------------------------------------------------------
;; Copy sprite data to OAM ($fe00-$fe9f), and use DMA!

;; First, copy DMA routine into HRAM.

;; How many bytes long is the DMA routine?
;; Since it's short, we can store the subroutine length in one register.
;; d will store the down-counter.
ld d, finishdma-dodma
;; hl holds the destination addr
ld hl, HRAM
;; bc holds the source addr
ld bc, dodma
copydmaloop:
    ld a, [bc]
    inc bc
    ld [hl], a
    inc hl
    dec d
    jr nz, copydmaloop
endcopydmaloop:
    jr finishdma

dodma:
    ld [DMA], a     ; 3 B
    ld a, $28      ; 2 B
waitdma:
    dec a           ; 1 B
    jr nz, waitdma  ; 2 B
    ret             ; 1 B
finishdma:

;; Second, copy the sprite data!
ld a, $02
call HRAM

;; -----------------------------------------------------------------------------
;; Done copying stuff, let's configure the display and turn it on.
    ;; enable BG display
    ld hl, LCDC
    set 0, [hl]
    ;; enable FG display
    set 5, [hl]
    ;; enable sprite display
    set 1, [hl]
    ;; enable display
    set 7, [hl]


;; -----------------------------------------------------------------------------
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