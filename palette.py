import numpy as np 

def hex_to_rgb(hex):
    h = hex.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def str_to_rgb(txt):
    try:
        tokens = txt.split(',')
        return (int(tokens[0]), int(tokens[1]), int(tokens[2]))
    except:
        pass
    try:
        return hex_to_rgb(txt)
    except:
        pass
    raise Exception("Invalid Format")

def hexlst_to_rgblst(lst):
    items = []
    for l in lst:
        items.append(hex_to_rgb(l))
    return items



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

    def __init__(self, colors, res = 100000, colors_map=None, color_correction = (255, 255, 255)):
        if colors_map is None:
            n = len(colors)
            colors_map = np.linspace(0,res,n, endpoint=True)
        self.res = res
        self.xp = colors_map
        self.fp = np.array(colors, dtype =np.int16)
        self.rp = self.fp[:,0]
        self.gp = self.fp[:,1]
        self.bp = self.fp[:,2]
        self.gama_val = np.array(Palette.GAMMA, dtype = np.int16) 
        self.gama_x = np.linspace(0, len(self.gama_val), len(self.gama_val), endpoint=False)
        self.correction = color_correction

    def set_res(self, res):
        self.xp = np.linspace(0,res,len(self.fp), endpoint=True)

    def interp_ext(self, data):
        val_r = np.interp(data, self.xp, self.rp)
        val_g = np.interp(data, self.xp, self.gp)
        val_b = np.interp(data, self.xp, self.bp)
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

    def get_color(self, data):
        return self.interp([data])[0]

    def interp_grb(self, data):
        val_r,val_g,val_b = self.interp_ext(data)
        return np.column_stack((val_g, val_r, val_b)).astype(np.int16)

    def from_color(color):
        return Palette([(0,0,0), color])

    def from_hex(hex_color):
        return Palette.from_color(hex_to_rgb(hex_color))

class Palettes:
    WHITE=hexlst_to_rgblst(["#000000", "#FFFFFF"])
    RED=hexlst_to_rgblst(["#000000", "#FF0000"])
    GREEN=hexlst_to_rgblst(["#000000", "#00FF00"])
    BLUE=hexlst_to_rgblst(["#000000", "#0000FF"])
    ALL=hexlst_to_rgblst([
        "#FF0000",
        "#FFFF00",
        "#00FF00",
        "#00FFFF",
        "#0000FF",
        "#FF00FF",
        "#FF0000",
    ])
    FIRE=hexlst_to_rgblst([
        "#000000",
        "#ff5a00",
        "#ffffff"
    ])
    FIRE_3= hexlst_to_rgblst([
        "#FFBB5C",
        "#FF9B50",
        "#E25E3E",
        "#C63D2F",
    ])
    FIRE_2 = hexlst_to_rgblst([
        "#ff0000",
        "#ff5a00",
        "#ff9a00",
        "#ffce00",
        "#ffce00",
        "#ffe808"
    ])
    

def test():
    colors = [
        (0x00, 0x00, 0x00),
        (0xFF, 0x00, 0x00),
        (0x00, 0xFF, 0x00),
        (0x00, 0x00, 0xFF),
        (0xFF, 0xFF, 0xFF)
    ]
    steps = [0,10,20,30,40]
    p = Palette(colors, 40)
    t = np.arange(0,41)
    val = p.interp(t)
    print(val)

if __name__ == "__main__":
    test()
