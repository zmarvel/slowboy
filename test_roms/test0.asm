include "header.asm"

org 0x0150
;;
;; Actual entry point
;;
loop:
nop
jr 0xfd ;; -3
jr loop
