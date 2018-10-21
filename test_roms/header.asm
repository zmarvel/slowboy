
;;
;; ROM HEADER
;;


SECTION "Start",ROM0[$0]
;ds $100, 0

SECTION "Header",ROM0[$100]
;;
;; Entry point
;;
nop
jp $0150

;;
;; Nintendo logo
;;
db $CE, $ED, $66, $66, $CC, $0D, $00, $0B
db $03, $73, $00, $83, $00, $0C, $00, $0D
db $00, $08, $11, $1F, $88, $89, $00, $0E
db $DC, $CC, $6E, $E6, $DD, $DD, $D9, $99
db $BB, $BB, $67, $63, $6E, $0E, $EC, $CC
db $DD, $DC, $99, $9F, $BB, $B9, $33, $3E

;;
;; Title
;;
db    "SLOWBOY", 1, 2, 3, 4


;;
;; Manufacturer code
;;
db 0, 0, 0, 0

;;
;; CGB flag
;;
db 0

;;
;; New licensee code
;;
db 0, 0

;;
;; SGB flag
;;
db 0

;;
;; Cartridge type: ROM only
;;
db 0

;;
;; ROM size: no ROM banking, 32 kB
;;
db 0

;;
;; RAM size: no external RAM
;;
db 0

;;
;; Destination code: non-Japanese
;;
db $01

;;
;; Old licensee code: use new licensee code
;;
db $33

;;
;; Mask ROM version number
;;
db 0

;;
;; Header checksum
;;
db 177

;;
;; Global checksum -- doesn't matter
;;
db 0, 0
