
CC = sdcc
AS = rgbasm
LD = rgblink
PP = m4

CFLAGS =
LDFLAGS =

ROMS = test0.gb \
       test1.gb \
       test2.gb \
       test3.gb \

OBJS = $(ROMS:%.gb=%.o)

BINS = tileset1.bin \
       tilemap1.bin \
       tileset2.bin \
       tilemap2.bin \

HEXS = $(patsubst %.gb,%.hex,$(ROMS)) \
       $(patsubst %.bin,%.hex,$(BINS))

all: $(ROMS) $(HEXS) $(BINS) $(OBJS)

%.asmpp: %.asm header.asm
	$(PP) $(PPFLAGS) $< > $@

tileset%.bin: img/tileset%.png scripts/image2tilemap.py
	python3 scripts/image2tilemap.py $< $@

tilemap%.bin: scripts/gentilemap%.py
	python3 $< $@

%.o: %.asmpp $(BINS)
	$(AS) $(ASFLAGS) \
		-o $@ $<

%.gb: %.o
	$(LD) $(LDFLAGS) \
		-o $@ $<

%.hex: %.gb
	hexdump -C $< > $@

%.hex: %.bin
	hexdump -C $< > $@

clean:
	rm -f $(ROMS) *.asmpp *.hex *.bin
