import numpy as np 

colors = [
    (0x00,0x00,0x00),
    (0xff,0x00,0x00),
    (0x00,0xff,0x00),
    (0x00,0x00,0xff)
]

class Palette:
    def __init__(self, colors, res = 100000, colors_map=None):
        if colors_map is None:
            n = len(colors)
            colors_map = np.linspace(0,res,n, endpoint=True)
        self.res = res
        self.xp = colors_map
        self.fp = np.array(colors, dtype =np.int16)
        self.rp = self.fp[:,0]
        self.gp = self.fp[:,1]
        self.bp = self.fp[:,2]

    def interp(self, data):
        val_r = np.interp(data, self.xp, self.rp)
        val_g = np.interp(data, self.xp, self.gp)
        val_b = np.interp(data, self.xp, self.bp)
        return np.column_stack((val_r, val_g, val_b)).astype(np.int16)

    

class SparkSim:

    def __init__(self, leds_count):
        self.rng = np.random.default_rng()
        self.leds_count = leds_count
        self.heat = np.zeros(self.leds_count, dtype = np.float16)
        self.leds = np.zeros([self.leds_count,3], dtype = np.float16)
        self.color = [
            (0x00, 0x00, 0x00),
            (0xff, 0x00, 0x00),
            (0x00, 0xff, 0x00),
            (0x00, 0x00, 0xff),
            (0xff, 0x00, 0xff),
            (0x00, 0xff, 0xff),
            (0xff, 0xff, 0xff),
        ]

        self.palette = Palette(self.color, 300)

    def update(self):
        hits = self.rng.integers(-1, 1, self.leds_count, dtype = np.int16, endpoint=True) * 3
        self.heat += hits
        self.heat = np.clip(self.heat, 0, self.palette.res)
        self.leds = self.palette.interp(self.heat)
        
if __name__ == "__main__":
    ss = SparkSim(5)
    while True:
        ss.update()
        print(ss.leds)


