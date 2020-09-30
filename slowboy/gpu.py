
from enum import Enum
import logging
from time import time
import functools as ft
from struct import unpack
import ctypes

from slowboy.util import ClockListener, add_s8
from slowboy.gfx import get_tile_surfaces, ltorgba, decode_2bit, decode_tile
from slowboy.interrupts import InterruptController, InterruptType
import sdl2
from sdl2 import SDL_BlitSurface, SDL_Rect, SDL_Error, SDL_ConvertSurfaceFormat
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


TWIDTH = 8
THEIGHT = 8
TSWIDTH = 128
TSHEIGHT = 128
TSWIDTH_TILES = TSWIDTH // TWIDTH
TSHEIGHT_TILES = TSHEIGHT // THEIGHT
SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144
SWIDTH_TILES = SCREEN_WIDTH // TWIDTH
SHEIGHT_TILES = SCREEN_HEIGHT // THEIGHT
BACKGROUND_WIDTH = 256
BACKGROUND_HEIGHT = 256
BGWIDTH_TILES = BACKGROUND_WIDTH // TWIDTH
BGHEIGHT_TILES = BACKGROUND_HEIGHT // THEIGHT
BACKGROUND_SIZE = (BACKGROUND_WIDTH, BACKGROUND_HEIGHT)
FOREGROUND_WIDTH = 256
FOREGROUND_HEIGHT = 256
FOREGROUND_SIZE = (FOREGROUND_WIDTH, FOREGROUND_HEIGHT)

SPRITETAB_SIZE = 40
SPRITETAB_ENTRY_SIZE = 4


def colorto8bit(c):
    if c > 3:
        raise ValueError

    return (c ^ 0x3) * 0x55


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
        # TODO may require changes for 8x16 sprites
        self._spritesurface = \
            sdl2.SDL_CreateRGBSurfaceWithFormat(0,
                                                TWIDTH*SPRITETAB_SIZE, THEIGHT,
                                                32, sdl2.SDL_PIXELFORMAT_RGBA32)
        self._spritetab = [(0, 0, 0, 0) for _ in range(SPRITETAB_SIZE)]
        self._tileset = sdl2.SDL_CreateRGBSurfaceWithFormat(0, 16*TWIDTH,
                                                            16*THEIGHT, 32,
                                                            sdl2.SDL_PIXELFORMAT_RGBA32)
            # sdl2.SDL_Surface
        self._fgtileset = None  # sdl2.SDL_Surface
        self._sprite_tiles = None  # sdl2.SDL_Surface
        self._palette = None
        self._sprite_palette0 = None
        self._sprite_palette1 = None
        self._sprite_palette = None
        self._needs_update = False
        self._needs_draw = False
        """Bitmap indicating which background tiles have been updated in
        :py:attr:GPU._tileset but not :py:attr:GPU._bgsurface"""
        self._stale_bgtiles = 0
        """Bitmap indicating which foreground tiles have been updated in
        :py:attr:GPU._fgtileset but not :py:attr:GPU._fgsurface"""
        self._stale_fgtiles = 0

        self._bgp = 0x00
        self._obp0 = 0x00
        self._obp1 = 0x00
        self._lcdc = 0x00
        self._stat = 0x00
        self._scy = 0x00
        self._scx = 0x00
        self._ly = 0x00
        self._lyc = 0x00
        self._mode = Mode.OAM_READ
        self._wy = 0x00
        self._wx = 0x00
        self.bgp = 0xfc         # BG palette data
        self.obp0 = 0xff        # Object palette 0 data
        self.obp1 = 0xff        # Object palette 1 data
        self.lcdc = 0x91        # LCD control register
        self.stat = 0           # LCD status register
        self.scy = 0            # Scroll y
        self.scx = 0            # Scroll x
        self.ly = 0             # LCD y-coordinate
        self.lyc = 0            # LY compare
        self.mode = Mode.OAM_READ
        self.wy = 0             # Window y position
        self.wx = 7             # Window x position - 7

        # initialize _palettes
        self.bgp = self._bgp
        self.obp0 = self._obp0
        self.obp1 = self._obp1

        self.mode = Mode.OAM_READ
        self._stat |= 0x03
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
        if self._lcdc == value:
            return
        self._lcdc = value
        #self.logger.debug('set LCDC to %#x', value)
        self.logger.info('set LCDC to %#x', value)
        self._update_vram('lcdc')

    @property
    def bgp(self):
        return self._bgp

    @bgp.setter
    def bgp(self, value):
        if self._bgp == value:
            return
        self._bgp = value
        self.logger.debug('set BGP to %#x', value)
        self._palette = [
            colorto8bit(value & 0x3),
            colorto8bit((value >> 2) & 0x3),
            colorto8bit((value >> 4) & 0x3),
            colorto8bit((value >> 6) & 0x3),
        ]
        self.logger.debug('set _palette to [%#x, %#x, %#x, %#x]',
                          self._palette[0], self._palette[1], self._palette[2], self._palette[3])
        self._update_vram('bgp')

    @property
    def obp0(self):
        return self._obp0

    @obp0.setter
    def obp0(self, value):
        if self._obp0 == value:
            return
        self._obp0 = value
        self.logger.debug('set OBP0 to %#x', value)
        # lower 2 bits aren't used for object palette (color 0 indicates
        # transparent)
        self._sprite_palette0 = [
            0xff,
            colorto8bit((value >> 2) & 0x3),
            colorto8bit((value >> 4) & 0x3),
            colorto8bit((value >> 6) & 0x3),
        ]
        self.logger.debug('set _sprite_palette0 to [%#x, %#x, %#x]',
                          self._sprite_palette0[1], self._sprite_palette0[2],
                          self._sprite_palette0[3])
        self._update_vram('obp0')

    @property
    def obp1(self):
        return self._obp1

    @obp1.setter
    def obp1(self, value):
        if self._obp1 == value:
            return
        self._obp1 = value
        self.logger.debug('set OBP1 to %#x', value)
        # lower 2 bits aren't used for object palette (color 0 indicates
        # transparent)
        self._sprite_palette1 = [
            0xff,
            colorto8bit((value >> 2) & 0x3),
            colorto8bit((value >> 4) & 0x3),
            colorto8bit((value >> 6) & 0x3),
        ]
        self.logger.debug('set _sprite_palette0 to [%#x, %#x, %#x]',
                          self._sprite_palette1[1], self._sprite_palette1[2],
                          self._sprite_palette1[3])
        self._update_vram('obp1')

    @property
    def scx(self):
        return self._scx

    @scx.setter
    def scx(self, value):
        if self._scx == value:
            return
        value &= 0xff
        self._scx = value
        self._update_vram('scx')
        self.logger.debug('set SCX to %#x', value)

    @property
    def scy(self):
        return self._scy

    @scy.setter
    def scy(self, value):
        if self._scy == value:
            return
        value &= 0xff
        self._scy = value
        self._update_vram('scy')
        self.logger.debug('set SCY to %#x', value)

    @property
    def ly(self):
        return self._ly

    @ly.setter
    def ly(self, value):
        """Set the LY register. As an optimization, this setter updates the
        stat register's LYC flag as well.
        """
        # We have to cheat and set _stat since the stat setter treats the LYC
        # flag as read-only
        if value == self.lyc:
            # LYC interrupt
            self._stat |= 1 << STAT_LYC_FLAG_OFFSET
            if self.interrupt_controller is not None and self.stat & STAT_LYC_IE_MASK:
                self.interrupt_controller.notify_interrupt(InterruptType.stat)
        else:
            self._stat &= ~STAT_LYC_FLAG_MASK
        self._ly = value
        self.logger.debug('set LY to %#x', value)

    @property
    def lyc(self):
        return self._lyc

    @lyc.setter
    def lyc(self, value):
        if value == self.ly:
            # LYC interrupt
            self._stat |= 1 << STAT_LYC_FLAG_OFFSET
            if self.interrupt_controller is not None and self.stat & STAT_LYC_IE_MASK:
                self.interrupt_controller.notify_interrupt(InterruptType.stat)
        else:
            self._stat &= ~STAT_LYC_FLAG_MASK
        self._lyc = value
        self.logger.debug('set LYC to %#x', value)

    @property
    def wy(self):
        return self._wy

    @wy.setter
    def wy(self, value):
        if self._wy == value:
            return
        self._wy = value
        self._update_vram('wy')
        self.logger.debug('set WY to %#x', value)

    @property
    def wx(self):
        return self._wx

    @wx.setter
    def wx(self, value):
        value -= 7
        if self._wy == value:
            return
        self._wx = value
        self._update_vram('wx')
        self.logger.debug('set WX to %#x', value)

    @property
    def stat(self):
        return self._stat

    @stat.setter
    def stat(self, new_stat):
        """STAT IO register.
        """
        old_stat = self._stat
        # Preserve coincidence and mode flags
        self._stat = (new_stat & ~(STAT_LYC_FLAG_MASK | STAT_MODE_MASK))\
                | (old_stat & (STAT_LYC_FLAG_MASK | STAT_MODE_MASK))
        # ly and mode setters will check this register for their interrupt
        # status and notify the interrupt controller if necessary
        self.logger.info('set STAT to %#x (%#x)', self._stat, new_stat)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, new_mode: Mode):
        """Set the GPU mode. As an optimization, this setter sets the stat
        MODE flag as well. This optimizes for programs that poll the STAT
        register, causing the stat getter to be called a lot.
        """
        stat = self.stat & ~STAT_MODE_MASK
        if self.interrupt_controller is not None:
            if (new_mode == Mode.OAM_READ or new_mode == Mode.OAM_VRAM_READ)\
               and stat & STAT_OAM_IE_MASK:
                self.interrupt_controller.notify_interrupt(InterruptType.stat)
            elif new_mode == Mode.V_BLANK:
                if stat & STAT_VBLANK_IE_MASK:
                    self.interrupt_controller.notify_interrupt(InterruptType.stat)
                self.interrupt_controller.notify_interrupt(InterruptType.vblank)
            elif new_mode == Mode.H_BLANK and stat & STAT_HBLANK_IE_MASK:
                self.interrupt_controller.notify_interrupt(InterruptType.stat)
        self._mode = new_mode
        # We have to "cheat" here to update the STAT mode flag--the stat setter
        # considers the mode flag read-only
        self._stat = stat | new_mode.value

    def log_regs(self, log=None):
        if log is None:
            log = self.logger.debug

        log('0xff40: LCDC: %#04x', self.lcdc)
        log('0xff41: STAT: %#04x', self.stat)
        log('0xff42: SCY : %#04x', self.scy)
        log('0xff43: SCX : %#04x', self.scx)
        log('0xff44: LY  : %#04x', self.ly)
        log('0xff45: LYC : %#04x', self.lyc)
        #log('0xff45: DMA : %#04x', self.dma)
        log('0xff47: BGP : %#04x', self.bgp)
        log('0xff48: OBP0: %#04x', self.obp0)
        log('0xff49: OBP1: %#04x', self.obp1)
        log('0xff4a: WY  : %#04x', self.wy)
        log('0xff4b: WX  : %#04x', self.wx)

    def _update_tilesets(self):
        """Update all tileset surfaces. Only needs to be called when pallete or
        tile data (in VRAM) changes.
        """

        for i in range(TSWIDTH_TILES*TSHEIGHT_TILES):
            self._update_tile(i)

    def _update_surfaces(self):
        self._update_bgsurface()
        self._update_fgsurface()
        self._update_sprite_surface()

    def _update_bgsurface(self):
        if self.lcdc & LCDC_BG_TILE_DISPLAY_SELECT_MASK:
            # 1=9C00-9FFF
            bgmap_start = 0x9c00 - VRAM_START
        else:
            # 0=9800-9BFF
            bgmap_start = 0x9800 - VRAM_START

        bgmap = self.vram[bgmap_start:bgmap_start+0x400]
        if self.lcdc & LCDC_BG_WINDOW_DATA_SELECT_MASK == 0:
            bgmap = bytes(map(ft.partial(add_s8, 128), bgmap))

        bgsurface = self._bgsurface
        stale_bgtiles = self._stale_bgtiles
        tile_size = (8, 8)
        width_tiles = BACKGROUND_WIDTH // TWIDTH
        height_tiles = BACKGROUND_HEIGHT // THEIGHT
        for i, tid in enumerate(bgmap):
            if (stale_bgtiles >> tid) & 1 == 0:
                continue
            x = (i % width_tiles) * TWIDTH
            y = (i // width_tiles) * THEIGHT
            tx = (tid % TSWIDTH_TILES) * TWIDTH
            ty = (tid // TSWIDTH_TILES) * THEIGHT
            src = SDL_Rect(tx, ty, 8, 8)
            dst = SDL_Rect(x, y, 8, 8)
            SDL_BlitSurface(self._tileset, src, bgsurface, dst)

        self._stale_bgtiles = 0

    def _update_fgsurface(self):

        if self.lcdc & LCDC_WINDOW_TILE_DISPLAY_SELECT_MASK:
            # 1=9C00-9FFF
            fgmap_start = 0x9c00 - VRAM_START
        else:
            # 0=9800-9BFF
            fgmap_start = 0x9800 - VRAM_START

        fgmap = self.vram[fgmap_start:fgmap_start+0x400]
        if self.lcdc & LCDC_BG_WINDOW_DATA_SELECT_MASK == 0:
            fgmap = bytes(map(ft.partial(add_s8, 128), fgmap))

        stale_fgtiles = self._stale_fgtiles
        fgsurface = self._fgsurface

        stale_fgtiles = self._stale_fgtiles
        tile_size = (8, 8)
        width_tiles = FOREGROUND_WIDTH // TWIDTH
        height_tiles = FOREGROUND_HEIGHT // THEIGHT
        for i, tid in enumerate(fgmap):
            if (stale_fgtiles >> tid) & 1 == 0:
                continue
            x = (i % width_tiles) * TWIDTH
            y = (i // width_tiles) * THEIGHT
            tx = (tid % TSWIDTH_TILES) * TWIDTH
            ty = (tid // TSWIDTH_TILES) * THEIGHT
            src = SDL_Rect(tx, ty, TWIDTH, THEIGHT)
            dst = SDL_Rect(x, y, TWIDTH, THEIGHT)
            SDL_BlitSurface(self._tileset, src, fgsurface, dst)

        self._stale_fgtiles = 0

    def _update_sprite_surface(self):
        """When the tileset or sprite palette is updated, refresh the decoded
        sprite surfaces.
        """

        for i in range(SPRITETAB_SIZE):
            ent = unpack('BBBB',
                         self.oam[i*SPRITETAB_ENTRY_SIZE:(i+1)*SPRITETAB_ENTRY_SIZE])
            self._spritetab[i] = ent
            ypos, xpos, tileid, attrs = ent
            x = i * TWIDTH
            y = 0
            tx = (tileid % TSWIDTH_TILES) * TWIDTH
            ty = (tileid // TSWIDTH_TILES) * THEIGHT
            src = SDL_Rect(tx, ty, TWIDTH, THEIGHT)
            dst = SDL_Rect(x, y, TWIDTH, THEIGHT)
            SDL_BlitSurface(self._tileset, src, self._spritesurface, dst)

    def draw(self, surface):
        """Returns True if surface was updated and False otherwise."""
        if self._needs_draw:
            self._needs_draw = False
        else:
            return False

        self.frame_count += 1
        if self.frame_count >= 20:
            t = time()
            diff = t - self.last_time
            self.fps = self.frame_count / diff
            self.last_time = t
            self.frame_count %= 20
            self.logger.info('{} fps'.format(self.fps))

        if self.lcdc & LCDC_DISPLAY_ENABLE_MASK == 0:
            dst = SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            color = sdl2.SDL_MapRGB(surface.format, 0xff, 0xff, 0xff)
            if sdl2.SDL_FillRect(surface, dst, color) < 0:
                raise sdl2.SDL_Error()
            return True

        if self._needs_update:
            #self._update_tilesets()
            #self._update_surfaces()
            self._needs_update = False

        # draw background
        #started = time()
        if self.lcdc & LCDC_BG_DISPLAY_MASK:
            src = SDL_Rect(self.scx, self.scy, SCREEN_WIDTH, SCREEN_HEIGHT)
            dst = SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            if SDL_BlitSurface(self._bgsurface, src, surface, dst) < 0:
                raise sdl2.SDL_Error()
            #if self.scx + SCREEN_WIDTH > BACKGROUND_WIDTH:
            #    src = SDL_Rect(0, self.scy, self.scx + SCREEN_WIDTH - BACKGROUND_WIDTH, SCREEN_HEIGHT)
            #    dst = SDL_Rect(
        else:
            dst = SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            color = sdl2.SDL_MapRGB(surface.format, 0xff, 0xff, 0xff)
            if sdl2.SDL_FillRect(surface, dst, color) < 0:
                raise sdl2.SDL_Error()
        #print('Took {} to draw background'.format(time() - started))

        # draw foreground
        #started = time()
        if self.lcdc & LCDC_WINDOW_DISPLAY_ENABLE_MASK:
           #converted = sdl2.SDL_ConvertSurfaceFormat(self._fgsurface,
           #                                          surface.format.contents.format,
           #                                          0)
           wx = self.wx
           wy = self.wy
           w = SCREEN_WIDTH - wx
           h = SCREEN_HEIGHT - wy
           src = SDL_Rect(0, 0, w, h)
           dst = SDL_Rect(wx, wy, w, h)
           if SDL_BlitSurface(self._fgsurface, src, surface, dst) < 0:
               raise sdl2.SDL_Error()
           #sdl2.SDL_FreeSurface(converted)
        #print('Took {} to draw foreground'.format(time() - started))

        # draw sprites
        #started = time()
        if self.lcdc & LCDC_SPRITE_DISPLAY_ENABLE_MASK:
            #converted = sdl2.SDL_ConvertSurfaceFormat(self._spritesurface,
            #                                          surface.format.contents.format,
            #                                          0)
            drew = 0
            for i, ent in enumerate(self._spritetab):
                ypos, xpos, tileid, attrs = ent
                # offscreen
                if ypos == 0 or ypos >= 160 or xpos == 0 or xpos >= 168:
                    continue
                drew += 1
                sx = i * TWIDTH
                sy = 0
                src = SDL_Rect(sx, sy, TWIDTH, THEIGHT)
                dx = xpos - 8
                dy = ypos - 16
                dst = SDL_Rect(dx, dy, TWIDTH, THEIGHT)
                if SDL_BlitSurface(self._spritesurface, src, surface, dst) < 0:
                    raise SDL_Error()
            #sdl2.SDL_FreeSurface(converted)
        #print('Took {} to draw {} sprites'.format(time() - started, drew))

        return True

    def dump_tile_memory(self, buf):
        for i in range(0x1800):
            buf[i] = self.get_vram(i)

    def dump_tileset(self, filename):
        print(type(self._tileset))
        if sdl2.SDL_SaveBMP(self._tileset, bytes(filename, encoding='utf-8')) < 0:
            raise SDL_Error()

    def dump_background(self, filename):
        if sdl2.SDL_SaveBMP(self._bgsurface, bytes(filename, encoding='utf-8')) < 0:
            raise SDL_Error()

    def dump_foreground(self, filename):
        if sdl2.SDL_SaveBMP(self._fgsurface, bytes(filename, encoding='utf-8')) < 0:
            raise SDL_Error()

    def dump_regs(self, write=print):
        regs = [
            ('BGP', self.bgp),
            ('OBP0', self.obp0),
            ('OBP1', self.obp1),
            ('LCDC', self.lcdc),
            ('STAT', self.stat),
            ('SCY', self.scy),
            ('SCX', self.scx),
            ('LY', self.ly),
            ('LYC', self.lyc),
            ('MODE', self.mode.value),
            ('WY', self.wy),
            ('WX', self.wx),
        ]

        for name, reg in regs:
            write('{}={:02x}'.format(name, reg))


    def present(self):
        pass
        #self.renderer.present()

    def notify(self, clock, cycles):
        self.mode_clock += cycles

        if self.mode == Mode.OAM_READ:
            if self.mode_clock >= 80:
                self.mode = Mode.OAM_VRAM_READ # 3
                self.mode_clock %= 80
        elif self.mode == Mode.OAM_VRAM_READ:
            if self.mode_clock >= 172:
                self.mode = Mode.H_BLANK # 0
                self.mode_clock %= 172
        elif self.mode == Mode.H_BLANK:
            if self.mode_clock >= 204:
                if self.ly == 143:
                    self.mode = Mode.V_BLANK # 1
                else:
                    self.mode = Mode.OAM_READ # 2
                self.ly += 1
                self.mode_clock %= 204
        elif self.mode == Mode.V_BLANK:
            if self.mode_clock % 204 == 0:
                self.ly += 1
            if self.mode_clock >= 4560:
                self._needs_draw = True
                self.mode = Mode.OAM_READ # 2
                self.mode_clock %= 4560
                self.ly = 0
        else:
            raise ValueError('Invalid GPU mode')

    def get_vram(self, addr):
        return self.vram[addr]

    def set_vram(self, addr, value):
        self.vram[addr] = value
        #self.logger.debug('set VRAM %#06x=%#06x', VRAM_START+addr, value)
        self._update_vram(addr, value)

    def _update_tile(self, tileid):
        """Update tile :py:obj:`i` in :py:attr:`GPU._bgtiles`.
        """
        if (self.lcdc & LCDC_WINDOW_DISPLAY_ENABLE_MASK == 0) and \
           (self.lcdc & LCDC_BG_DISPLAY_MASK == 0) and \
           (self.lcdc & LCDC_WINDOW_DISPLAY_ENABLE_MASK == 0):
            return

        # TODO changeme
        #assert 0 <= tileid < 0x100
        # Skip invalid tiles--this means vram got updated for an unselected
        # tileset.
        if tileid < 0 or tileid >= 0x100:
            return

        tile_idx = tileid * 16
        encoded_tile = self.vram[tile_idx:tile_idx+16]
        # Decode the tile from 2-bit color to RGBA
        decoded_tile = decode_tile(encoded_tile, self._palette)
        #decoded_tile = GBTileset(encoded_tile, (8, 8), (8, 8)).to_rgb(self._palette).data
        rgba_data = bytearray(len(decoded_tile)*4)
        for i, b in enumerate(decoded_tile):
            c = ltorgba(b)
            rgba_data[4*i+0] = (c >> 24) & 0xff
            rgba_data[4*i+1] = (c >> 16) & 0xff
            rgba_data[4*i+2] = (c >> 8) & 0xff
            rgba_data[4*i+3] = c & 0xff
        tile_surface = sdl2.SDL_CreateRGBSurfaceWithFormatFrom(
            bytes(rgba_data),
            TWIDTH, THEIGHT,
            32, TWIDTH*4,
            sdl2.SDL_PIXELFORMAT_RGBA32)
        if not tile_surface:
            print(sdl2.SDL_GetError())
            raise Exception
        x = (tileid % TSWIDTH_TILES) * TWIDTH
        y = (tileid // TSWIDTH_TILES) * THEIGHT
        #print(x, y)
        dst = SDL_Rect(x, y, TWIDTH, THEIGHT)
        if sdl2.SDL_BlitSurface(tile_surface, None, self._tileset, dst) < 0:
            print(sdl2.SDL_GetError())
            raise Exception

        sdl2.SDL_FreeSurface(tile_surface)

        self._stale_bgtiles |= (1 << tileid)
        self._stale_fgtiles |= (1 << tileid)

    def _update_vram(self, addr, value=None):
        """Update internal dataset (decoded tiles, etc).

        If BG display is disabled (lcdc), :py:attr:`GPU._update_tile` will do
        nothing. When BG display is enabled, all background tile surfaces will
        be decoded.

        If FG display is disabled, :py:attr:`GPU._update_fgtile` will also do
        nothing. When FG/window display is enabled, all foreground tile surfaces
        will be decoded.

        Same with sprite display.
        """

        if isinstance(addr, str):
            # Register
            if addr == 'lcdc':
                self._update_tilesets()
                self._update_surfaces()
                self._update_sprite_surface()
            elif addr == 'bgp':
                self._update_tilesets()
                self._update_bgsurface()
                self._update_fgsurface()
            elif addr == 'obp0':
                self._update_sprite_surface()
            elif addr == 'obp1':
                self._update_sprite_surface()
            elif addr == 'scx' or addr == 'scy':
                pass
            elif addr == 'wx' or addr == 'wy':
                pass
        elif isinstance(addr, int) and self.lcdc & LCDC_DISPLAY_ENABLE_MASK \
                    and (self.lcdc & LCDC_WINDOW_DISPLAY_ENABLE_MASK or self.lcdc & LCDC_BG_DISPLAY_MASK):
            # VRAM
            addr += VRAM_START
            # Tilemap data
            if 0x9800 <= addr < 0xa000:
                if self.lcdc & LCDC_BG_TILE_DISPLAY_SELECT_MASK == 0:
                    # 0x9800-9bff
                    tile = addr - 0x9800
                else:
                    # 0x9c00-0x9fff
                    tile = addr - 0x9c00
                if self.lcdc & LCDC_WINDOW_TILE_DISPLAY_SELECT_MASK == 0:
                    # 0x9800-9bff
                    tile = addr - 0x9800
                else:
                    # 0x9c00-0x9fff
                    tile = addr - 0x9c00
                #self._update_tile(tile)
                self._update_surfaces()
            # Tile data
            elif 0x8000 <= addr < 0x9800:
                if self.lcdc & LCDC_BG_WINDOW_DATA_SELECT_MASK == 0:
                    # 0x8800-0x97ff
                    tile = (addr - 0x8800) // 16
                else:
                    # 0x8000-0x8fff
                    tile = (addr - 0x8000) // 16
                #self._update_tilesets()
                #print(self.lcdc & LCDC_BG_WINDOW_DATA_SELECT_MASK, hex(addr), tile, value)
                self._update_tile(tile)


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
        old = self.oam[addr]
        self.oam[addr] = value
        self.logger.debug('set OAM %#06x=%#06x', OAM_START+addr, value)
        if old != value:
            self._update_sprite_surface()

    @property
    def enabled(self):
        return (self.lcdc & LCDC_DISPLAY_ENABLE_MASK) or (self.lcdc & LCDC_WINDOW_DISPLAY_ENABLE_MASK) or (self.lcdc & LCDC_SPRITE_DISPLAY_ENABLE_MASK)

    @enabled.setter
    def enabled(self, value):
        if value:
            self.lcdc |= 1 << LCDC_DISPLAY_ENABLE_OFFSET
        else:
            self.lcdc &= 0xff ^ (1 << LCDC_DISPLAY_ENABLE_OFFSET)
