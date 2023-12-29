import numpy as np
from util.config import DataClass

@DataClass(name="Color")
class Color:
    def __new__(cls, r=None, g=None, b=None, value=None, *kwargs) -> tuple:
        if value is not None:
            return cls.parse_colors(value)
        return (r,g,b)
    
    def from_hex(hex) -> tuple:
        h = hex.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def from_str(txt) -> tuple:
        try:
            tokens = txt.split(',')
            return (int(tokens[0]), int(tokens[1]), int(tokens[2]))
        except:
            pass
        try:
            return Color.__from_str(txt)
        except:
            pass
        raise Exception("Invalid Format")

    def parse_colors(colors) -> (tuple | list):
        if isinstance(colors, str):
            color = Color.from_str(colors)
            return color
        elif isinstance(colors, (list,tuple)):
            if len(colors) == 3 and isinstance(colors[0], (int, float, complex)):
                return (int(colors[0]), int(colors[1]), int(colors[2]))
            else:
                tmp = colors
                colors = []
                for n in tmp:
                    colors.append(Color.parse_colors(n))
                return colors
        return colors

    def __from_str(value) -> tuple:
        colors_map = {
            "BLACK":"#000000",
            "WHITE":"#FFFFFF",
            "RED":"#FF0000",
            "GREEN":"#00FF00",
            "BLUE":"#0000FF",
            "ORANGE":"#FF8000",
            "YELLOW":"#FFFF00",
            "LIME":"#80FF00",
            "AQUA":"#00FF80",
            "CYAN":"#00FFFF",
            "OCEAN":"#0080FF",
            "VIOLET":"#8000FF",
            "MAGENTA":"#FF00FF",
            "RASPBERRY":"#FF0080"
        }
        value = value.upper()
        if value in colors_map:
            value = colors_map[value]
        return Color.from_hex(value)

@DataClass(name="Palette")
class Palette:
    GAMMA = [
        0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
        0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,
        1,  1,  1,  1,  1,  1,  1,  1,  1,  2,  2,  2,  2,  2,  2,  2,
        2,  3,  3,  3,  3,  3,  3,  3,  4,  4,  4,  4,  4,  5,  5,  5,
        5,  6,  6,  6,  6,  7,  7,  7,  7,  8,  8,  8,  9,  9,  9, 10,
        10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
        17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
        25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
        37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
        51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
        69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
        90, 92, 93, 95, 96, 98, 99,101,102,104,105,107,109,110,112,114,
        115,117,119,120,122,124,126,127,129,131,133,135,137,138,140,142,
        144,146,148,150,152,154,156,158,160,162,164,167,169,171,173,175,
        177,180,182,184,186,189,191,193,196,198,200,203,205,208,210,213,
        215,218,220,223,225,228,231,233,236,239,241,244,247,249,252,255
    ]

    def __init__(self, colors:str|tuple|list, res = 65536, colors_map=None, color_correction = (255, 255, 255), **kwargs):
        colors = Color.parse_colors(colors)
        if isinstance(colors, (tuple)):
            colors = [(0,0,0), colors]

        color_correction = Color.parse_colors(color_correction)

        if colors_map is None:
            n = len(colors)
            colors_map = np.linspace(0,res,n, endpoint=True)

        self.res = res
        self.colors_map = colors_map
        self.colors = np.array(colors, dtype =np.int16)
        self.colors_red_val = self.colors[:,0]
        self.colors_green_val = self.colors[:,1]
        self.colors_blue_val = self.colors[:,2]
        self.gama_val = np.array(Palette.GAMMA, dtype = np.int16)
        self.gama_x = np.linspace(0, len(self.gama_val), len(self.gama_val), endpoint=False)
        self.correction = color_correction

    def set_res(self, res):
        self.colors_map = np.linspace(0,res,len(self.fp), endpoint=True)

    def interp_ext(self, data):
        val_r = np.interp(data, self.colors_map, self.colors_red_val)
        val_g = np.interp(data, self.colors_map, self.colors_green_val)
        val_b = np.interp(data, self.colors_map, self.colors_blue_val)
        return (val_r, val_g, val_b)

    def correct_color(self, data):
        data = np.array(data)
        data = (data * self.correction)/255
        data = np.clip(data, 0, 255)
        return data.astype(np.int16)

    def apply_gammas(self, data):
        return np.interp(data, self.gama_x, self.gama_val).astype(np.int16)

    def interp(self, data):
        return np.column_stack(self.interp_ext(data)).astype(np.int16)

    def apply_gamma(self, color):
        return self.apply_gammas([color])[0]

    def get_color(self, data:int):
        return self.interp([data])[0]

    def from_color(color:tuple):
        return Palette([(0,0,0), color])

    def from_hex(hex_color : str):
        return Palette.from_color(Color.from_str(hex_color))

