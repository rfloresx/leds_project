import numpy as np
import random

from util.config import DataClass
from effects.base import SimBase

class HeatBase(SimBase):
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
    
@DataClass(name="Sparks")
class Sparks(HeatBase):
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

@DataClass(name="Roll")
class Roll(HeatBase):
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

@DataClass(name="Fade")
class Fade(HeatBase):
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
        self.pixels.fill(self.color)
        self.pixels.setBrightness(int(255*self.brightness))
        self.pixels.show()
    
    def get_color(self):
        # self.
        return super().get_color()

