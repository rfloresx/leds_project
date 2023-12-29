import numpy as np
import util.logger as logger

class SimBase:
    def __init__(self, pixels, palette, **kwargs):
        self.rng = np.random.default_rng()
        self.pixels = pixels
        try:
            self.pixels.activate(self)
        except AttributeError as e:
            logger.error(e)
        
        self.palette = palette
        self.leds_count = kwargs.get('leds_count', len(self.pixels))
        self.leds = np.zeros([self.leds_count,3], dtype = np.int16)

    def __del__(self):
        try:
            self.pixels.release(self)
        except AttributeError as e:
            logger.error(e)

    def update(self):
        self.pixels[:] = self.get_leds()
        self.pixels.show()

    def get_leds(self):
        self.leds = self.palette.correct_color(self.leds)
        return self.leds