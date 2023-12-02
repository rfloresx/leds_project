import sys
import board
import palette
import numpy as np 
import neopixel
import random
import time

class SimBase:
    def __init__(self, **kwargs):
        self.rng = np.random.default_rng()
        self.leds_count = kwargs.get('leds_count')
        self.leds = np.zeros([self.leds_count,3], dtype = np.float16)
    
    def update(self):
        pass

class HeatSim(SimBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.min_heat = kwargs.get('min_heat', 0)
        self.max_heat = kwargs.get('max_heat', 255)
        self.heat = self.rng.integers(self.min_heat, self.max_heat, self.leds_count, dtype=np.int16)

        self.palette = kwargs.get('palette')

    def update(self):
        super().update()

    def get_leds(self):
        self.heat = np.clip(self.heat, self.min_heat, self.max_heat)
        self.leds = self.palette.interp(self.heat)
        return self.leds

class FireSim(HeatSim):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cold_down = kwargs.get('cold_down', 0)
        self.sparks = kwargs.get('sparks', 3)
        self.spark = kwargs.get('spark', self.max_heat - self.max_heat//10)

    def update(self):
        super().update()
        self.heat += self.cold_down
        for n in range(self.sparks):
            j = random.randint(0,self.leds_count-1)
            self.heat[j] = self.spark


class SparkSim:
    def __init__(self, leds_count):
        self.rng = np.random.default_rng()
        self.leds_count = leds_count
        self.res = 3000
        # self.heat = np.zeros(self.leds_count, dtype = np.float16)
        self.heat = self.rng.integers(0, self.res, self.leds_count, dtype = np.int16)
        self.leds = np.zeros([self.leds_count,3], dtype = np.float16)
        self.color = [
            (0x00, 0x00, 0x00),
            # (0xff, 0x00, 0x00),
            # (0x00, 0xff, 0x00),
            # (0x00, 0x00, 0xff),
            # (0xff, 0x00, 0xff),
            # (0x00, 0xff, 0xff),
            (0xff, 0xff, 0xff),
        ]
        self.scale = 30
        self.palette = palette.Palette(self.color, self.res)

    def update(self):
        hits = self.rng.integers(-1, 1, self.leds_count, dtype = np.int16, endpoint=True) * self.scale
        self.heat += hits
        self.heat = np.clip(self.heat, 0, self.palette.res)
        self.leds = self.palette.interp(self.heat)

class HexColors:
    COLOR_MAP = [
        ("BLACK","#000000"),
        ("WHITE","#FFFFFF"),
        ("RED","#FF0000"),
        ("GREEN","#00FF00"),
        ("BLUE","#0000FF"),
        ("ORANGE","#FF8000"),
        ("YELLOW","#FFFF00"),
        ("LIME","#80FF00"),
        ("AQUA","#00FF80"),
        ("CYAN","#00FFFF"),
        ("OCEAN","#0080FF"),
        ("VIOLET","#8000FF"),
        ("MAGENTA","#FF00FF"),
        ("RASPBERRY","#FF0080")
    ]
    BLACK="#000000"
    WHITE="#FFFFFF"
    RED="#FF0000"
    GREEN="#00FF00"
    BLUE="#0000FF"
    ORANGE="#FF8000"
    YELLOW="#FFFF00"
    LIME="#80FF00"
    AQUA="#00FF80"
    CYAN="#00FFFF"
    OCEAN="#0080FF"
    VIOLET="#8000FF"
    MAGENTA="#FF00FF"
    RASPBERRY="#FF0080"

    def get(index):
        return HexColors.COLOR_MAP[index][1]
    def get_name(index):
        return HexColors.COLOR_MAP[index][0]



if __name__ == "__main__":
    leds_count = 100
    # p = palette.Palette.from_hex("#FF0000")
    p = palette.Palette(palette.Palettes.ALL, color_correction = (255, 120, 120))
    # p = palette.Palette([(255,0,0), (255, 255,0)], color_correction = (255, 120, 180))

    p.set_res(leds_count)
    ss = FireSim(leds_count = leds_count, palette=p, cold_down=-1, sparks=1, spark=255, min_heat=100, max_heat=240)
    pixels = neopixel.NeoPixel(board.D18, leds_count, brightness=1, auto_write=False, pixel_order=neopixel.RGB)

    if False:
        delta = np.linspace(0,leds_count, leds_count)            
        colors = p.interp(delta)
        colors_fixed = p.correct_color(colors)
        pixels[:] = colors_fixed
        pixels.show()
        for line in sys.stdin:
            try:
                index = int(line)
                print(f"Sellected {index}")
                print(f"Color{colors[index]} Color_G{colors_fixed[index]}")
                break
            except:
                print(f"Err: {line}")
    
    if False:
        for line in sys.stdin:
            if "q" == line.rstrip():
                break
            try:
                rgb = palette.str_to_rgb(line)
                color = p.correct_color([rgb])[0]
                pixels.fill(color)
                pixels.show()
            except Exception as e:
                print(F"Err: {line} {e}")
                raise e
    if True:
        for line in sys.stdin:
            try:
                index = int(line)
                hex_color = HexColors.get(index)
                color = palette.str_to_rgb(hex_color)
                color = p.correct_color([color])[0]
                print(f"{index} {color} {hex_color} {HexColors.get_name(index)}")
                pixels.fill(color)
                pixels.show()

            except Exception as e:
                print(f"Err: {line} {e}")
                raise e
# 125, 30, 0 Orange
# 125,53,0 Yello
# 0,55,10 
# 0,55,40 # Cyan 


# time.sleep(100)
# for i in range(1000):
        
        

        # print(i, c, g)
        # pixels[0:25] = [c for i in range(25)]
        # pixels[25:50] = [g for i in range(25)]
        # pixels.show()
        # time.sleep(.1)
    
        # heat = np.roll(heat, 1)
        # heat[0] = i
        # pixels[:] = p.interp(heat)
        # pixels.show()
        # time.sleep(.1)
        #255,80,0 = YELLOW
        # 
        # self.leds = p.interp_grb(i)
    # while True:
        
    #     ss.update()
    #     pixels[:] = ss.get_leds()
    #     pixels.show()
