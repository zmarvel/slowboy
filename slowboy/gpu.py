
LCDC_DISPLAY_ENABLE_OFFSET = 7
LCDC_DISPLAY_ENABLE = 1 << LCDC_DISPLAY_ENABLE_OFFSET
LCDC_WINDOW_TILE_DISPLAY_SELECT_OFFSET = 6
LCDC_WINDOW_TILE_DISPLAY_SELECT = 1 << LCDC_WINDOW_TILE_DISPLAY_SELECT_OFFSET
LCDC_WINDOW_DISPLAY_ENABLE_OFFSET = 5
LCDC_WINDOW_DISPLAY_ENABLE = 1 << LCDC_WINDOW_DISPLAY_ENABLE_OFFSET 
LCDC_BG_WINDOW_DATA_SELECT_OFFSET = 4
LCDC_BG_WINDOW_DATA_SELECT = 1 << LCDC_BG_WINDOW_DATA_SELECT_OFFSET
LCDC_BG_TILE_DISPLAY_SELECT_OFFSET = 3
LCDC_BG_TILE_DISPLAY_SELECT = 1 << LCDC_BG_TILE_DISPLAY_SELECT_OFFSET
LCDC_OBJ_SIZE_8x16_OFFSET = 2
LCDC_OBJ_SIZE_8x16 = 1 << LCDC_OBJ_SIZE_8x16_OFFSET
LCDC_OBJ_DISPLAY_ENABLE_OFFSET = 1
LCDC_OBJ_DISPLAY_ENABLE = 1 << LCDC_OBJ_DISPLAY_ENABLE_OFFSET
LCDC_BG_DISPLAY_OFFSET = 0
LCDC_BG_DISPLAY = 1 << LCDC_BG_DISPLAY_OFFSET

STAT_LYC_INTERRUPT_ENABLE_OFFSET = 6
STAT_LYC_INTERRUPT_ENABLE = 1 << STAT_LYC_OFFSET
STAT_OAM_INTERRUPT_ENABLE_OFFSET = 5
STAT_OAM_INTERRUPT_ENABLE = 1 << STAT_OAM_INTERRUPT_ENABLE_OFFSET
STAT_VBLANK_INTERRUPT_ENABLE_OFFSET = 4
STAT_VBLANK_INTERRUPT_ENABLE = 1 << STAT_VBLANK_INTERRUPT_ENABLE_OFFSET 
STAT_HBLANK_INTERRUPT_ENABLE_OFFSET = 3
STAT_HBLANK_INTERRUPT_ENABLE = 1 << STAT_HBLANK_INTERRUPT_ENABLE_OFFSET
STAT_LYC_OFFSET = 2
STAT_MODE_OFFSET = 0



class GPU():
    def __init__(self):
        self._lcdc = 0  # LCD control register
        self._stat = 0  # LCD status register
        self._scy = 0   # Scroll y
        self._scx = 0   # Scroll x
        self._ly = 0    # LCD y-coordinate
        self._lyc = 0   # LY compare
        self._wy = 0    # Window y position
        self._wx = 0    # Window x position - 7
        self._bgp = 0   # BG palette data
        self._obp0 = 0  # Object palette 0 data
        self._obp1 = 0  # Object palette 1 data
        
        self.vram = bytearray(8*1024)   # 0x8000-0x9fff
        self.oam = bytearray(0xa0)      # 0xfe00-0xfe9f
    
    @property
    def lcdc(self):
        return self._lcdc

    @lcdc.setter
    def lcdc(self, value):
        self._lcdc = value

    @property
    def stat(self):
        return self._stat

