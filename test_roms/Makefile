
CC = sdcc
AS = z80asm
PP = m4

CFLAGS =
LDFLAGS =

ROMS = test0.gb \
       test1.gb

BINS = tileset1.bin \
       tilemap1.bin

HEXS = $(patsubst %.gb,%.hex,$(ROMS)) \
       $(patsubst %.bin,%.hex,$(BINS))

all: $(ROMS) $(HEXS) $(BINS)

%.asmpp: %.asm header.asm
	$(PP) $(PPFLAGS) $< > $@

%.gb: %.asmpp $(BINS)
	$(AS) $(ASFLAGS) \
	    --list=$(patsubst %.asmpp,%.lst,$<) \
	    --label=$(patsubst %.asmpp,%.lbl,$<) -o $@ $<

%.hex: %.gb
	hexdump -C $< > $@

%.hex: %.bin
	hexdump -C $< > $@

tileset1.bin: img/tileset1.png scripts/image2tilemap.py
	python3 scripts/image2tilemap.py $< $@

tilemap1.bin: scripts/gentilemap1.py
	python3 scripts/gentilemap1.py $@

clean:
	rm -f $(ROMS) *.asmpp *.bin
