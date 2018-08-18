
from enum import Enum
import logging
from time import time
import functools as ft

from slowboy.util import ClockListener, add_s8
from slowboy.gfx import GBTileset, get_tile_surfaces, ltorgba
from slowboy.interrupts import InterruptController, InterruptType
import sdl2
from sdl2 import SDL_BlitSurface
from sdl2.ext import Color

VRAM_START = 0x8000
OAM_START = 0xfe00

LCDC_DISPLAY_ENABLE_OFFSET = 7
LCDC_DISPLAY_ENABLE_MASK = 1 << LCDC_DISPLAY_ENABLE_OFFSET
LCDC_WINDOW_TILE_DISPLAY_SELECT_OFFSET = 6
LCDC_WINDOW_TILE_DISPLAY_SELECT_MASK = 1 << LCDC_WINDOW_TILE_DISPLAY_SELECT_OFFSET
LCDC_WINDOW_DISPLAY_ENABLE_OFFSET = 5
LCDC_WINDOW_DISPLAY_ENABLE_MASK = 1 << LCDC_WINDOW_DISPLAY_ENABLE_OFFSET
LCDC_BG_WINDOW_DATA_SELECT_OFFSET = 4
LCDC_BG_WINDOW_DATA_SELECT_MASK = 1 << LCDC_BG_WINDOW_DATA_SELECT_OFFSET
LCDC_BG_TILE_DISPLAY_SELECT_OFFSET = 3
LCDC_BG_TILE_DISPLAY_SELECT_MASK = 1 << LCDC_BG_TILE_DISPLAY_SELECT_OFFSET
LCDC_SPRITE_SIZE_OFFSET = 2
LCDC_SPRITE_DISPLAY_ENABLE_OFFSET = 1
LCDC_SPRITE_DISPLAY_ENABLE_MASK = 1 << LCDC_SPRITE_DISPLAY_ENABLE_OFFSET
LCDC_BG_DISPLAY_OFFSET = 0
LCDC_BG_DISPLAY_MASK = 1 << LCDC_BG_DISPLAY_OFFSET

STAT_LYC_IE_OFFSET = 6
STAT_LYC_IE_MASK = 1 << STAT_LYC_IE_OFFSET
STAT_OAM_IE_OFFSET = 5
STAT_OAM_IE_MASK = 1 << STAT_OAM_IE_OFFSET
STAT_VBLANK_IE_OFFSET = 4
STAT_VBLANK_IE_MASK = 1 << STAT_VBLANK_IE_OFFSET
STAT_HBLANK_IE_OFFSET = 3
STAT_HBLANK_IE_MASK = 1 << STAT_HBLANK_IE_OFFSET
STAT_LYC_FLAG_OFFSET = 2
STAT_LYC_FLAG_MASK = 1 << STAT_LYC_FLAG_OFFSET
STAT_MODE_OFFSET = 0
STAT_MODE_MASK = 0x03


SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144
BACKGROUND_WIDTH = 256
BACKGROUND_HEIGHT = 256
BACKGROUND_SIZE = (BACKGROUND_WIDTH, BACKGROUND_HEIGHT)


class Mode(Enum):
    H_BLANK = 0
    V_BLANK = 1
    OAM_READ = 2
    OAM_VRAM_READ = 3


class GPU(ClockListener):
    def __init__(self, logger=None, log_level=logging.INFO, interrupt_controller=None):
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger.getChild(__class__.__name__)
        if log_level is not None:
            self.logger.setLevel(log_level)

        self.interrupt_controller = interrupt_controller

        self.vram = bytearray(0xa000 - 0x8000)   # 0x8000-0x9fff
        self.oam = bytearray(0xfea0 - 0xfe00)    # 0xfe00-0xfe9f
        self._bgsurfaces = []
        self._fgsurfaces = []
        self._bgsurface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, BACKGROUND_WIDTH, BACKGROUND_HEIGHT,
                                                              32, sdl2.SDL_PIXELFORMAT_RGBA32)
        self._fgsurface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, BACKGROUND_WIDTH, BACKGROUND_HEIGHT,
                                                              32, sdl2.SDL_PIXELFORMAT_RGBA32)
        self._bgtileset = None  # sdl2.SDL_Surface
        self._fgtileset = None  # sdl2.SDL_Surface
        self._sprite_tiles = None  # sdl2.SDL_Surface
        self._bgpalette = None
        self._sprite_palette0 = None
        self._sprite_palette1 = None
        self._sprite_palette = None
        self._needs_update = False

        self._bgp = 0xfc   # BG palette data
        self._obp0 = 0xff  # Object palette 0 data
        self._obp1 = 0xff  # Object palette 1 data
        self._lcdc = 0x91  # LCD control register
        self._stat = 0  # LCD status register
        self._scy = 0   # Scroll y
        self._scx = 0   # Scroll x
        self._ly = 0
        self._lyc = 0
        self._mode = Mode.OAM_READ
        self._wy = 0    # Window y position
        self._wx = 0    # Window x position - 7
        self._dma = 0

        self.ly = 0     # LCD y-coordinate
        self.lyc = 0    # LY compare

        # initialize _palettes
        self.bgp = self._bgp
        self.obp0 = self._obp0
        self.obp1 = self._obp1

        self.mode = Mode.OAM_READ
        self.stat |= 0x03
        self.mode_clock = 0

        self.last_time = time()
        self.frame_count = 0
        self.fps = 0

    def load_interrupt_controller(self, ic: InterruptController):
        self.interrupt_controller = ic

    def load_vram(self, vram):
        assert len(vram) == 0xa000 - 0x8000
        self.vram = bytearray(vram)

    def load_oam(self, oam):
        assert len(oam) == 0x100
        self.oam = bytearray(oam)

    @property
    def lcdc(self):
        return self._lcdc

    @lcdc.setter
    def lcdc(self, value):
        self._lcdc = value
        #self.logger.debug('set LCDC to %#x', value)
        self.logger.info('set LCDC to %#x', value)
        self._update_vram('lcdc')

    @property
    def bgp(self):
        return self._bgp

    @bgp.setter
    def bgp(self, value):
        self._bgp = value
        self.logger.debug('set BGP to %#x', value)
        self._bgpalette = [
            (value & 0x3) * 85,
            ((value >> 2) & 0x3) * 85,
            ((value >> 4) & 0x3) * 85,
            ((value >> 6) & 0x3) * 85,
        ]
        self.logger.debug('set _bgpalette to [%#x, %#x, %#x, %#x]',
                          self._bgpalette[0], self._bgpalette[1], self._bgpalette[2], self._bgpalette[3])
        self._update_vram('bgp')

    @property
    def obp0(self):
        return self._obp0

    @obp0.setter
    def obp0(self, value):
        self._obp0 = value
        self.logger.debug('set OBP0 to %#x', value)
        self._sprite_palette0 = [
            (value & 0x3) * 85,
            ((value >> 2) & 0x3) * 85,
            ((value >> 4) & 0x3) * 85,
            ((value >> 6) & 0x3) * 85,
        ]
        self.logger.debug('set _sprite_palette0 to [%#x, %#x, %#x, %#x]',
                          self._sprite_palette0[0], self._sprite_palette0[1],
                          self._sprite_palette0[2], self._sprite_palette0[3])
        self._update_vram('obp0')

    @property
    def obp1(self):
        return self._obp1

    @obp1.setter
    def obp1(self, value):
        self._obp1 = value
        self.logger.debug('set OBP1 to %#x', value)
        self._sprite_palette1 = [
            (value & 0x3) * 85,
            ((value >> 2) & 0x3) * 85,
            ((value >> 4) & 0x3) * 85,
            ((value >> 6) & 0x3) * 85,
        ]
        self.logger.debug('set _sprite_palette0 to [%#x, %#x, %#x, %#x]',
                          self._sprite_palette1[0], self._sprite_palette1[1],
                          self._sprite_palette1[2], self._sprite_palette1[3])
        self._update_vram('obp1')

    @property
    def scx(self):
        return self._scx

    @scx.setter
    def scx(self, value):
        value &= 0xff
        self._scx = value
        self._update_vram('scx')
        self.logger.debug('set SCX to %#x', value)

    @property
    def scy(self):
        return self._scy

    @scy.setter
    def scy(self, value):
        value &= 0xff
        self._scy = value
        self._update_vram('scy')
        self.logger.debug('set SCY to %#x', value)

    @property
    def ly(self):
        return self._ly

    @ly.setter
    def ly(self, value):
        if value == self.lyc:
            # LYC interrupt
            self.stat |= 1 << STAT_LYC_FLAG_OFFSET
            if self.interrupt_controller is not None:
                self.interrupt_controller.notify_interrupt(InterruptType.stat)
        else:
            self.stat &= 0xff ^ (1 << STAT_LYC_FLAG_OFFSET)
        self._ly = value
        self.logger.debug('set LY to %#x', value)

    @property
    def lyc(self):
        return self._lyc

    @lyc.setter
    def lyc(self, value):
        if value == self.ly:
            # LYC interrupt
            self.stat |= 1 << STAT_LYC_FLAG_OFFSET
            if self.interrupt_controller is not None:
                self.interrupt_controller.notify_interrupt(IterruptType.stat)
        else:
            self.stat &= 0xff ^ (1 << STAT_LYC_FLAG_OFFSET)
        self._lyc = value
        self.logger.debug('set LYC to %#x', value)

    @property
    def wy(self):
        return self._wy

    @wy.setter
    def wy(self, value):
        self._wy = value
        self._update_vram('wy')
        self.logger.debug('set WY to %#x', value)

    @property
    def wx(self):
        return self._wx

    @wx.setter
    def wx(self, value):
        self._wx = value
        self._update_vram('wx')
        self.logger.debug('set WX to %#x', value)

    @property
    def stat(self):
        stat = self._stat & ~(STAT_LYC_FLAG_MASK | STAT_MODE_MASK)
        if self.ly == self.lyc:
            stat |= 1 << STAT_LYC_FLAG_OFFSET
        stat |= self.mode.value << STAT_MODE_OFFSET
        self._stat = stat
        return stat

    @stat.setter
    def stat(self, value):
        """STAT IO register.

        This setter should be called to update mode, and it will trigger
        interrupts as necessary. If the LYC flag is set to 1, the corresponding
        interrupt will also be triggered.
        """
        interrupts = (value >> 3) & 0xf
        old_mode = self._stat & 0x3
        mode = value & 0x3
        if (old_mode ^ mode) != 0:
            # mode has changed -- new interrupts
            if mode == 0 and interrupts & 0x1:
                # hblank
                self.interrupt_controller.notify_interrupt(InterruptType.stat)
            elif mode == 1:
                # vblank
                if self.interrupt_controller is not None:
                    if interrupts & 0x2:
                        self.interrupt_controller.notify_interrupt(InterruptType.stat)
                    self.interrupt_controller.notify_interrupt(InterruptType.vblank)
            elif mode == 2 and interrupts & 0x4:
                # oam read
                self.interrupt_controller.notify_interrupt(InterruptType.stat)
            elif mode < 0 or mode > 3:
                raise ValueError('Invalid mode {}'.format(mode))

        old_lyc_flag = (self._stat >> STAT_LYC_FLAG_OFFSET) & 1
        lyc_flag = (value >> STAT_LYC_FLAG_OFFSET) & 1
        if (old_lyc_flag ^ lyc_flag) != 0:
            if lyc_flag and interrupts & STAT_LYC_IE_MASK:
                # ly coincidence
                self.interrupt_controller.notify_interrupt(InterruptType.stat)
        else:
            value &= ~STAT_LYC_FLAG_MASK

        self._stat = value
        self.logger.debug('set STAT to %#x', value)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        stat = self.stat 
        if value == Mode.OAM_READ and stat & STAT_OAM_IE_MASK and \
           self.interrupt_controller is not None:
            self.interrupt_controller.notify_interrupt(InterruptType.stat)
        elif value == Mode.V_BLANK and stat & STAT_VBLANK_IE_MASK and \
                self.interrupt_controller is not None:
            self.interrupt_controller.notify_interrupt(InterruptType.stat)
        elif value == Mode.H_BLANK and stat & STAT_HBLANK_IE_MASK and \
                self.interrupt_controller is not None:
            self.interrupt_controller.notify_interrupt(InterruptType.stat)
        self._mode = value
        self.stat = stat 

    @property
    def dma(self):
        self.logger.error('not implemented: DMA')
        return self._dma

    @dma.setter
    def dma(self, value):
        value = value & 0xff
        self.logger.debug('set DMA to %#x', value)
        self.logger.error('not implemented: DMA')
        self._dma = value

    def log_regs(self, log=None):
        if log is None:
            log = self.logger.debug

        log('0xff40: LCDC: %#04x', self.lcdc)
        log('0xff41: STAT: %#04x', self.stat)
        log('0xff42: SCY : %#04x', self.scy)
        log('0xff43: SCX : %#04x', self.scx)
        log('0xff44: LY  : %#04x', self.ly)
        log('0xff45: LYC : %#04x', self.lyc)
        log('0xff45: DMA : %#04x', self.dma)
        log('0xff47: BGP : %#04x', self.bgp)
        log('0xff48: OBP0: %#04x', self.obp0)
        log('0xff49: OBP1: %#04x', self.obp1)
        log('0xff4a: WY  : %#04x', self.wy)
        log('0xff4b: WX  : %#04x', self.wx)

    def _update_tilesets(self):
        # TODO allow only updating one tileset
        if self.lcdc & LCDC_BG_WINDOW_DATA_SELECT_MASK:
            # 1=8000-8FFF
            start = 0x8000-VRAM_START
        else:
            # 0=8800-97FF
            start = 0x8800-VRAM_START
        #self._bgtileset = GBTileset(self.vram[start:start+0x1000],
        #                      (256, 256), (8, 8))
        if self._bgtileset:
            sdl2.SDL_FreeSurface(self._bgtileset)

        rgb_tileset = GBTileset(self.vram[start:start+0x1000], (256, 256), (8, 8)).to_rgb(self._bgpalette)
        rgb_data = bytearray(len(rgb_tileset.data)*4)
        for i, b in enumerate(rgb_tileset.data):
            c = ltorgba(b)
            rgb_data[4*i+0] = (c >> 24) & 0xff
            rgb_data[4*i+1] = (c >> 16) & 0xff
            rgb_data[4*i+2] = (c >> 8) & 0xff
            rgb_data[4*i+3] = c & 0xff

        w, h = rgb_tileset.size
        self._tileset_size = rgb_tileset.size
        self._bgtileset = sdl2.SDL_CreateRGBSurfaceWithFormatFrom(bytes(rgb_data), w, h, 32, w*4,  sdl2.SDL_PIXELFORMAT_RGBA32)
        if not self._bgtileset:
            raise sdl2.SDL_Error()
        self._fgtileset = self._bgtileset

        return self._bgtileset

    def _update_surfaces(self):
        return
        # TODO allow only updating one surface
        for surf in self._bgsurfaces:
            sdl2.SDL_FreeSurface(surf)
        rgba_bgpalette = list(map(ltorgba, self._bgpalette))
        self._bgsurfaces = list(get_tile_surfaces(self._bgtileset.to_rgb(self._bgpalette).split_tiles(),
                                                  rgba_bgpalette))

        def ltorgba_fg(c):
            alpha = 0x00 if c == 0 else 0xff
            return ltorgba(c, alpha=alpha)

        for surf in self._fgsurfaces:
            sdl2.SDL_FreeSurface(surf)
        rgba_fgpalette = list(map(ltorgba_fg, self._bgpalette))
        #rgba_fgpalette[0] = 0xffffff00
        self._fgsurfaces = list(get_tile_surfaces(self._fgtileset.to_rgb(self._bgpalette).split_tiles(),
                                                  rgba_fgpalette))
        return self._bgsurfaces

    def _update_bgsurface(self):
        if self.lcdc & LCDC_BG_TILE_DISPLAY_SELECT_MASK:
            # 1=9C00-9FFF
            bgmap_start = 0x9c00 - VRAM_START
        else:
            # 0=9800-9BFF
            bgmap_start = 0x9800 - VRAM_START

        if self.lcdc & LCDC_WINDOW_TILE_DISPLAY_SELECT_MASK:
            # 1=9C00-9FFF
            fgmap_start = 0x9c00 - VRAM_START
        else:
            # 0=9800-9BFF
            fgmap_start = 0x9800 - VRAM_START

        bgmap = self.vram[bgmap_start:bgmap_start+0x400]

        fgmap = self.vram[fgmap_start:fgmap_start+0x400]
        if self.lcdc & LCDC_BG_WINDOW_DATA_SELECT_MASK == 0:
            bgmap = bytes(map(ft.partial(add_s8, 128), bgmap))
            fgmap = bytes(map(ft.partial(add_s8, 128), fgmap))

        bgsurface = self._bgsurface
        fgsurface = self._fgsurface
        fgsurfaces = self._fgsurfaces
        tile_size = (8, 8)
        tile_width, tile_height = tile_size
        width_tiles = BACKGROUND_WIDTH // tile_width
        #src = sdl2.SDL_Rect(0, 0, 256, 256)
        #dst = sdl2.SDL_Rect(0, 0, 256, 256)
        #SDL_BlitSurface(self._bgtileset, src, bgsurface, dst)
        height_tiles = BACKGROUND_HEIGHT // tile_height
        #ts_width_tiles = self._tileset_size[0] // tile_width
        for i, tid in enumerate(bgmap):
            x = (i % width_tiles) * tile_width
            y = (i // width_tiles) * tile_height
            tx = (tid % width_tiles) * tile_width
            ty = (tid // width_tiles) * tile_height
            src = sdl2.SDL_Rect(tx, ty, 8, 8)
            dst = sdl2.SDL_Rect(x, y, 8, 8)
            #converted = sdl2.SDL_ConvertSurfaceFormat(bgsurfaces[tid], bgsurface.contents.format.contents.format, 0)
            #if SDL_BlitSurface(converted, src, bgsurface, dst) < 0:
            #    raise sdl2.SDL_Error()
            #sdl2.SDL_FreeSurface(converted)
            SDL_BlitSurface(self._bgtileset, src, bgsurface, dst)

            #fgtid = fgmap[i]
            #tx = (fgtid % width_tiles) * tile_width
            #ty = (fgtid // width_tiles) * tile_height
            #src = sdl2.SDL_Rect(tx, ty, 8, 8)
            #converted = sdl2.SDL_ConvertSurfaceFormat(fgsurfaces[fgtid], fgsurface.contents.format.contents.format, 0)
            #if SDL_BlitSurface(converted, src, fgsurface, dst) < 0:
            #    raise sdl2.SDL_Error()
            #sdl2.SDL_FreeSurface(converted)

    def draw(self, surface):
        """Returns True if surface was updated and False otherwise."""

        if self.mode_clock < 4560:
            return False

        if not self.lcdc & LCDC_DISPLAY_ENABLE_MASK:
            dst = sdl2.SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            color = sdl2.SDL_MapRGB(surface.format, 0xff, 0xff, 0xff)
            if sdl2.SDL_FillRect(surface, dst, color) < 0:
                raise sdl2.SDL_Error()
            return True

        if self._needs_update:
            self._update_tilesets()
            self._update_surfaces()
            self._update_bgsurface()
            self._needs_update = False

        if self.lcdc & LCDC_BG_DISPLAY_MASK:
            converted = sdl2.SDL_ConvertSurfaceFormat(self._bgsurface, surface.format.contents.format, 0)
            src = sdl2.SDL_Rect(self.scx, self.scy, SCREEN_WIDTH, SCREEN_HEIGHT)
            dst = sdl2.SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            if SDL_BlitSurface(converted, src, surface, dst) < 0:
                raise sdl2.SDL_Error()
            sdl2.SDL_FreeSurface(converted)
        else:
            dst = sdl2.SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            color = sdl2.SDL_MapRGB(surface.format, 0xff, 0xff, 0xff)
            if sdl2.SDL_FillRect(surface, dst, color) < 0:
                raise sdl2.SDL_Error()

        # if self.lcdc & LCDC_WINDOW_DISPLAY_ENABLE_MASK:
        #     converted = sdl2.SDL_ConvertSurfaceFormat(self._fgsurface, surface.format.contents.format, 0)
        #     src = sdl2.SDL_Rect(self.wx, self.wy+7, SCREEN_WIDTH, SCREEN_HEIGHT)
        #     dst = sdl2.SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        #     if SDL_BlitSurface(converted, src, surface, dst) < 0:
        #         raise sdl2.SDL_Error()
        #     sdl2.SDL_FreeSurface(converted)

        self.frame_count += 1
        if self.frame_count >= 60:
            t = time()
            diff = t - self.last_time
            self.fps = self.frame_count / diff
            self.last_time = t
            self.frame_count %= 60
            self.logger.info('{} fps'.format(self.fps))

        return True


    def present(self):
        pass
        #self.renderer.present()

    def notify(self, clock, cycles):
        self.mode_clock += cycles

        if self.mode == Mode.OAM_READ:
            if self.mode_clock >= 80:
                self.mode = Mode.OAM_VRAM_READ # 3
                self.stat ^= 0x3
                self.stat |= self.mode.value
                self.mode_clock %= 80
        elif self.mode == Mode.OAM_VRAM_READ:
            if self.mode_clock >= 172:
                self.mode = Mode.H_BLANK # 0
                self.stat ^= 0x3
                self.stat |= self.mode.value
                self.mode_clock %= 172
        elif self.mode == Mode.H_BLANK:
            if self.mode_clock >= 204:
                if self.ly == 143:
                    self.mode = Mode.V_BLANK # 1
                    self.stat ^= 0x3
                    self.stat |= self.mode.value
                else:
                    self.mode = Mode.OAM_READ # 2
                    self.stat ^= 0x3
                    self.stat |= self.mode.value
                self.ly += 1
                self.mode_clock %= 204
        elif self.mode == Mode.V_BLANK:
            if self.mode_clock % 204 == 0:
                self.ly += 1
            if self.mode_clock >= 4560:
                self.mode = Mode.OAM_READ # 2
                self.stat ^= 0x3
                self.stat |= self.mode.value
                self.mode_clock %= 4560
                self.ly = 0
        else:
            raise ValueError('Invalid GPU mode')

    def get_vram(self, addr):
        return self.vram[addr]

    def set_vram(self, addr, value):
        self.vram[addr] = value
        self.logger.debug('set VRAM %#06x=%#06x', VRAM_START+addr, value)
        self._update_vram(addr)

    def _update_vram(self, addr):
        """Update internal dataset (decoded tiles, etc)"""
        # what is this for? TODO
        #self.vram[addr] = val
        #hi, lo = self.vram[addr], self.vram[addr+1]
        #offset = (addr // 2) * 8
        #for i in range(8):
        #    self.vram[offset+i] = (((hi >> i) & 1) << 1) | ((lo >> i) & 1)
        #if self.enabled:
            #print('update vram', addr)
        self._needs_update = True
            #self._update_tilesets()
            #self._update_surfaces()
            #self._update_bgsurface()

    def get_oam(self, addr):
        return self.oam[addr]

    def set_oam(self, addr, value):
        self.oam[addr] = value
        self.logger.debug('set OAM %#06x=%#06x', OAM_START+addr, value)
        self._update_oam()

    def _update_oam(self):
        pass

    @property
    def enabled(self):
        return (self.lcdc & LCDC_DISPLAY_ENABLE_MASK) or (self.lcdc & LCDC_WINDOW_DISPLAY_ENABLE_MASK) or (self.lcdc & LCDC_SPRITE_DISPLAY_ENABLE_MASK)

    @enabled.setter
    def enabled(self, value):
        if value:
            self.lcdc |= 1 << LCDC_DISPLAY_ENABLE_OFFSET
        else:
            self.lcdc &= 0xff ^ (1 << LCDC_DISPLAY_ENABLE_OFFSET)
