
VRAM_START = 0x8000
OAM_START = 0xfe00

LCDC_DISPLAY_ENABLE_OFFSET = 7
LCDC_WINDOW_TILE_DISPLAY_SELECT_OFFSET = 6
LCDC_WINDOW_DISPLAY_ENABLE_OFFSET = 5
LCDC_BG_WINDOW_DATA_SELECT_OFFSET = 4
LCDC_BG_WINDOW_DATA_SELECT_MASK = 1 << LCDC_BG_WINDOW_DATA_SELECT_OFFSET
LCDC_BG_TILE_DISPLAY_SELECT_OFFSET = 3
LCDC_BG_TILE_DISPLAY_SELECT_MASK = 1 << LCDC_BG_TILE_DISPLAY_SELECT_OFFSET
LCDC_SPRITE_SIZE_OFFSET = 2
LCDC_SPRITE_DISPLAY_ENABLE_OFFSET = 1
LCDC_BG_DISPLAY_OFFSET = 0

STAT_LYC_INTERRUPT_ENABLE_OFFSET = 6
STAT_OAM_INTERRUPT_ENABLE_OFFSET = 5
STAT_VBLANK_INTERRUPT_ENABLE_OFFSET = 4
STAT_HBLANK_INTERRUPT_ENABLE_OFFSET = 3
STAT_LYC_FLAG_OFFSET = 2
STAT_MODE_OFFSET = 0

from enum import Enum

from slowboy.util import ClockListener
from slowboy.gfx import GBTileset, RGBTileset, get_tile_surfaces
import sdl2
from sdl2 import SDL_BlitSurface


BACKGROUND_WIDTH = 256
BACKGROUND_HEIGHT = 256

#def irgb_average(iterable):
#    """Takes an iterable, which will be consumed in groups of 3 (so the iterable
#    should have a length divisible by 3). This function is a generator of the
#    average of these RGB values.
#    """
#    try:
#        iterable = iter(iterable)
#        while True:
#            r = next(iterable)
#            g = next(iterable)
#            b = next(iterable)
#            yield (r + g + b) // 3
#    except StopIteration:
#        pass
#
#def i2bit(iterable):
#    """Consumes an iterable of byte values and generates pairs of bytes
#    representing 8 pixels.
#    """
#    try:
#        iterable = iter(iterable)
#        while True:
#            hi = 0
#            lo = 0
#            for i in range(8):
#                c = next(iterable) // 64
#                hi |= (c >> 1) << i
#                lo |= (c & 1) << i
#            yield hi
#            yield lo
#    except StopIteration:
#        pass
#
#def i2bitdecode(iterator):
#    iterator = iter(iterator)
#    counts = defaultdict(lambda: 0)
#    try:
#        while True:
#            hi = next(iterator)
#            lo = next(iterator)
#            for i in range(8):
#                c = (lo >> i) & 1
#                c |= ((hi >> i) & 1) << 1
#                color = palette[c]
#                counts[(color.r, color.g, color.b)] += 1
#                yield color
#    except StopIteration:
#        print(counts)
#        raise StopIteration()

class Mode(Enum):
    H_BLANK = 0
    V_BLANK = 1
    OAM_READ = 2
    OAM_VRAM_READ = 3

class GPU(ClockListener):
    def __init__(self):
        self.lcdc = 0   # LCD control register
        self.stat = 0   # LCD status register
        self.scy = 0    # Scroll y
        self.scx = 0    # Scroll x
        self.ly = 0     # LCD y-coordinate
        self.lyc = 0    # LY compare
        self.wy = 0     # Window y position
        self.wx = 0     # Window x position - 7
        self.bgp = 0    # BG palette data
        self.obp0 = 0   # Object palette 0 data
        self.obp1 = 0   # Object palette 1 data

        self.mode = Mode.OAM_READ
        self.mode_clock = 0
        
        self.vram = bytearray(0xa000 - 0x8000)   # 0x8000-0x9fff
        self.oam = bytearray(0xfea0 - 0xfe00)    # 0xfe00-0xfe9f

    def load_vram(self, vram):
        assert len(vram) == 0xa000 - 0x8000
        self.vram = bytearray(vram)

    def load_oam(self, oam):
        assert len(oam) == 0x100
        self.oam = bytearray(oam)

    def draw(self, surface):
        def torgba(c):
            assert c < 4
            return ((c << 6) | (c << 4) | (c << 2) | c)
        bgpalette = [
            torgba(self.bgp & 0x3),
            torgba((self.bgp >> 2) & 0x3),
            torgba((self.bgp >> 4) & 0x3),
            torgba((self.bgp >> 6) & 0x3),
        ]
        # for fg, idx 0 is transparent
        fgpalette = [
            self.bgp & 0x3,
            (self.bgp >> 2) & 0x3,
            (self.bgp >> 4) & 0x3,
            (self.bgp >> 6) & 0x3,
        ]
        obpalette0 = [
            self.obp0 & 0x3,
            (self.obp0 >> 2) & 0x3,
            (self.obp0 >> 4) & 0x3,
            (self.obp0 >> 6) & 0x3,
        ]
        obpalette1 = [
            self.obp1 & 0x3,
            (self.obp1 >> 2) & 0x3,
            (self.obp1 >> 4) & 0x3,
            (self.obp1 >> 6) & 0x3,
        ]

        if self.lcdc & LCDC_BG_TILE_DISPLAY_SELECT_MASK:
            # 1=9C00-9FFF
            bgmap_start = 0x9c00 - VRAM_START
        else:
            # 0=9800-9BFF
            bgmap_start = 0x9800 - VRAM_START
        bgmap = self.vram[bgmap_start:bgmap_start+0x400]

        if self.lcdc & LCDC_BG_WINDOW_DATA_SELECT_MASK:
            # 1=8000-8FFF
            bgtileset = GBTileset(self.vram[0x8000-VRAM_START:0x8000-VRAM_START+0x1000],
                                  (256, 256), (8, 8))
        else:
            # 0=8800-97FF
            bgtileset = GBTileset(self.vram[0x8800-VRAM_START:0x8800-VRAM_START+0x1000],
                                  (256, 256), (8, 8))

        bgsurfaces = list(get_tile_surfaces(bgtileset.to_rgb(bgpalette).split_tiles(),
                                           format=surface.format.contents.format))

        tile_size = (8, 8)
        tile_width, tile_height = tile_size
        width_tiles = BACKGROUND_WIDTH // tile_width
        height_tiles = BACKGROUND_HEIGHT // tile_height
        for i, tid in enumerate(bgmap):
            x = (i % width_tiles) * tile_width
            y = (i // width_tiles) * tile_height
            src = sdl2.SDL_Rect(0, 0, 8, 8)
            dst = sdl2.SDL_Rect(x, y, 8, 8)
            if SDL_BlitSurface(bgsurfaces[tid], src, surface, dst) < 0:
                raise sdl2.SDL_Error()

        for surf in bgsurfaces:
            sdl2.SDL_FreeSurface(surf)

    def present(self):
        pass
        #self.renderer.present()

    def notify(self, clock, cycles):
        self.mode_clock += cycles

        if self.mode == Mode.OAM_READ:
            if self.mode_clock >= 80:
                self.mode = Mode.OAM_VRAM_READ
                self.stat |= 0x3
                self.mode_clock = 0
        elif self.mode == Mode.OAM_VRAM_READ:
            if self.mode_clock >= 172:
                self.mode = Mode.H_BLANK
                self.stat &= 0xff ^ 0x3
                self.mode_clock = 0
        elif self.mode == Mode.H_BLANK:
            if self.mode_clock >= 204:
                self.mode = Mode.V_BLANK
                self.stat &= 0xff ^ 0x3
                self.stat |= 0x01
                self.mode_clock = 0
        elif self.mode == Mode.V_BLANK:
            if self.mode_clock >= 4560:
                self.mode = Mode.OAM_READ
                self.stat &= 0xff ^ 0x3
                self.stat |= 0x02
                self.mode_clock = 0
        else:
            raise ValueError('Invalid GPU mode')

    # TODO: maintain an internal dataset for the background, window, and sprites
    # so we don't have to go back and forth between 2-bit
    def get_vram(self, addr):
        return self.vram[addr]

    def set_vram(self, addr, value):
        self.vram[addr] = value
        self._update_vram(addr, value)

    def _update_vram(self, addr, val):
        self.vram[addr] = val
        hi, lo = self.vram[addr], self.vram[addr+1]
        offset = (addr // 2) * 8
        for i in range(8):
            self.vram[offset+i] = (((hi >> i) & 1) << 1) | ((lo >> i) & 1)

    def get_oam(self, addr):
        return self.oam[addr]

    def set_oam(self, addr, value):
        self.oam[addr] = value
        self._update_oam_sprites()

    @property
    def enabled(self):
        return (self.lcdc >> LCDC_DISPLAY_ENABLE_OFFSET) & 1

    @enabled.setter
    def enabled(self, value):
        if value:
            self.lcdc |= 1 << LCDC_DISPLAY_ENABLE_OFFSET
        else:
            self.lcdc &= ~LCDC_DISPLAY_ENABLE_OFFSET

    @property
    def window_map(self):
        return (self.lcdc >> LCDC_WINDOW_TILE_DISPLAY_SELECT_OFFSET) & 1

    @window_map.setter
    def window_map(self, value):
        if value == 1: # 9C00-9FFF
            self.lcdc |= 1 << LCDC_WINDOW_TILE_DISPLAY_SELECT_OFFSET
        else: # 9800-9BFF
            self.lcdc &= ~LCDC_WINDOW_TILE_DISPLAY_SELECT_OFFSET

    @property
    def window_enabled(self):
        return (self.lcdc >> LCDC_WINDOW_DISPLAY_ENABLE_OFFSET) & 1

    @window_enabled.setter
    def window_enabled(self, value):
        if value:
            self.lcdc |= 1 << LCDC_WINDOW_DISPLAY_ENABLE_OFFSET
        else:
            self.lcdc &= ~LCDC_WINDOW_DISPLAY_ENABLE_OFFSET

    @property
    def bg_window_data(self):
        return (self.lcdc >> LCDC_BG_WINDOW_DATA_SELECT_OFFSET) & 1

    @bg_window_data.setter
    def bg_window_data(self, value):
        if value == 1: # 8000-8FFF
            self.lcdc |= 1 << LCDC_BG_WINDOW_DATA_SELECT_OFFSET
        else: # 8800-97FF
            self.lcdc &= ~LCDC_BG_WINDOW_DATA_SELECT_OFFSET

    @property
    def bg_map(self):
        return (self.lcdc >> LCDC_BG_TILE_DISPLAY_SELECT_OFFSET) & 1

    @bg_map.setter
    def bg_map(self, value):
        if value == 1: # 9C00-9FFF
            self.lcdc |= 1 << LCDC_BG_TILE_DISPLAY_SELECT_OFFSET
        else: # 9800-9BFF
            self.lcdc &= ~LCDC_BG_TILE_DISPLAY_SELECT_OFFSET

    @property
    def sprite_size(self):
        return (self.lcdc >> LCDC_BG_TILE_DISPLAY_SELECT_OFFSET) & 1

    @sprite_size.setter
    def sprite_size(self, value):
        if value == 1:
            self.lcdc |= 1 << LCDC_SPRITE_SIZE_OFFSET
        else:
            self.lcdc &= ~LCDC_SPRITE_SIZE_OFFSET

    @property
    def sprite_enabled(self):
        return (self.lcdc >> LCDC_SPRITE_DISPLAY_ENABLE_OFFSET)

    @sprite_enabled.setter
    def sprite_enabled(self, value):
        if value:
            self.lcdc |= 1 << LCDC_SPRITE_DISPLAY_ENABLE_OFFSET
        else:
            self.lcdc &= ~LCDC_SPRITE_DISPLAY_ENABLE_OFFSET

    @property
    def lyc_interrupt_enabled(self):
        return (self.stat >> STAT_LYC_INTERRUPT_ENABLE_OFFSET) & 1

    @lyc_interrupt_enabled.setter
    def lyc_interrupt_enabled(self, value):
        if value:
            self.stat |= 1 << STAT_LYC_INTERRUPT_ENABLE_OFFSET
        else:
            self.stat &= ~STAT_LYC_INTERRUPT_ENABLE_OFFSET

    @property
    def oam_interrupt_enabled(self):
        return (self.stat >> STAT_OAM_INTERRUPT_ENABLE_OFFSET) & 1

    @oam_interrupt_enabled.setter
    def oam_interrupt_enabled(self, value):
        if value:
            self.stat |= 1 << STAT_OAM_INTERRUPT_ENABLE_OFFSET
        else:
            self.stat &= ~STAT_OAM_INTERRUPT_ENABLE_OFFSET

    @property
    def vblank_interrupt_enabled(self):
        return (self.stat >> STAT_VBLANK_INTERRUPT_ENABLE_OFFSET) & 1

    @vblank_interrupt_enabled.setter
    def vblank_interrupt_enabled(self, value):
        if value:
            self.stat |= 1 << STAT_VBLANK_INTERRUPT_ENABLE_OFFSET
        else:
            self.stat &= ~STAT_VBLANK_INTERRUPT_ENABLE_OFFSET

    @property
    def hblank_interrupt_enabled(self):
        return (self.stat >> STAT_HBLANK_INTERRUPT_ENABLE_OFFSET) & 1

    @hblank_interrupt_enabled.setter
    def hblank_interrupt_enabled(self, value):
        if value:
            self.stat |= 1 << STAT_HBLANK_INTERRUPT_ENABLE_OFFSET
        else:
            self.stat &= ~STAT_HBLANK_INTERRUPT_ENABLE_OFFSET

    @property
    def lyc_flag(self):
        return (self.stat >> STAT_LYC_FLAG_OFFSET) & 1

    @property
    def mode_flag(self):
        return (self.stat >> STAT_MODE_OFFSET) & 3
