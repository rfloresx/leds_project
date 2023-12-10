import palette
import numpy as np 
import random
import led_strip


class SimBase:
    def __init__(self, pixels, palette, **kwargs):
        self.rng = np.random.default_rng()
        self.pixels = pixels
        try:
            self.pixels.activate(self)
        except AttributeError:
            pass
        
        self.palette = palette
        self.leds_count = kwargs.get('leds_count', len(self.pixels))
        self.leds = np.zeros([self.leds_count,3], dtype = np.int16)

    def __del__(self):
        try:
            self.pixels.release(self)
        except AttributeError:
            pass

    def update(self):
        self.pixels[:] = self.get_leds()
        self.pixels.show()

    def get_leds(self):
        self.leds = self.palette.correct_color(self.leds)
        return self.leds
    
class HeatSim(SimBase):
    def __init__(self, min_heat = 0, max_heat = None, **kwargs):
        super().__init__(**kwargs)
        self.min_heat = min_heat
        self.max_heat = max_heat if max_heat is not None else self.palette.res
        self.heat = np.zeros(self.leds_count, dtype=np.float16)

    def update(self):
        super().update()

    def get_leds(self):
        self.heat = np.clip(self.heat, self.min_heat, self.max_heat)
        self.leds = self.palette.interp(self.heat)
        return super().get_leds()

class FireSim(HeatSim):
    def __init__(self, cold_down = 0, sparks = 3, spark = None, **kwargs):
        super().__init__(**kwargs)
        self.cold_down = cold_down
        self.sparks = sparks
        self.spark = spark if spark is not None else self.max_heat
        self.cold_down_val = 0
        self.sparks_val = 0

    def update(self):
        super().update()
        self.cold_down_val += self.cold_down
        if self.cold_down_val > 1 or self.cold_down_val < -1:
            self.heat += self.cold_down_val
            self.cold_down_val = 0

        self.sparks_val += self.sparks
        if self.sparks_val > 1:
            for n in range(int(self.sparks_val)):
                j = random.randint(0,self.leds_count-1)
                self.heat[j] = self.spark
            self.sparks_val = 0

class RollSim(HeatSim):
    def __init__(self, speed = 1, **kwargs):
        super().__init__(**kwargs)
        self.speed = speed
        self.current = self.min_heat

    def update(self):
        super().update()
        self.current += self.speed
        if self.current > self.max_heat:
            self.current = self.min_heat
        elif self.current < self.min_heat:
            self.current = self.max_heat
        self.heat = np.roll(self.heat, 1)
        self.heat[0] = self.current

class FadeSim(HeatSim):
    def __init__(self, color = (255, 255, 255), **kwargs):
        super().__init__(**kwargs)
        self.color = color
        for n in range(self.leds_count):
            self.leds[n] = self.color
        self.brightness = 0
        self.dir = 1
        self.scale = .001

    def update(self):
        self.brightness += self.dir * self.scale

        if self.brightness < 0.0:
            self.brightness = 0.0
            self.dir = 1
        if self.brightness > 1.0:
            self.brightness = 1.0
            self.dir = -1
        val = int(255*self.brightness)
        print(f"val {val}")
        self.pixels.fill(self.color)
        self.pixels.setBrightness(int(255*self.brightness))
        self.pixels.show()
    
    def get_color(self):
        # self.
        return super().get_color()


CLASS_LIST = {
    "HeatSim":HeatSim,
    "FireSim":FireSim,
    "RollSim":RollSim,
    "FadeSim":FadeSim
}


def main():
    option = 'fade'
    color_correction = (255, 255, 255)
    # color_correction = (255, 120, 120)

    leds_count = 1000
    res = 255
    # p = palette.Palette.from_hex("#FF0000")
    # plt = palette.Palette(palette.Palettes.ALL, color_correction = (255, 120, 120), res=res)
    # p = palette.Palette([(255,0,0), (255, 255,0)], color_correction = (255, 120, 120))
    plt = palette.Palette([(0,0,0), (250, 250,255)], color_correction = color_correction, res = res)

    pixels = led_strip.LedStrip(led_strip.GPIO.D18, leds_count, brightness=125, strip_type=led_strip.RGB)
    match option:
        case 'sparks':
            sim = FireSim(pixels = pixels, palette=plt, cold_down=-3, sparks=1, min_heat=15)
        case 'roll':
            sim =  RollSim(pixels = pixels, palette=plt, speed=1)
        case 'fade':
            sim =  FadeSim(pixels = pixels, palette=plt, speed=1)
        case _:
            sim = None
    if sim is not None:
        while True:
            sim.update()
            # pixels[:] = sim.get_leds()
            # pixels.show()
            # time.sleep(.05)

if __name__ == "__main__":
    main()
