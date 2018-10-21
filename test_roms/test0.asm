include "header.asm"

SECTION "EntryPoint",ROM0[$150]
;;
;; Actual entry point
;;
loop:
nop
jr $fd ;; -3
jr loop
