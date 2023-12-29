# from rpi_ws281x import PixelStrip, ws
from .rpi_ws281x_ext import PixelStrip, ws, get_strip_type
from util.config import DataClass

import numbers
import numpy as np

@DataClass(name="GpioInfo")
class GpioInfo:
    def __init__(self, pin, freq=800000, dma=10, invert=False, channel=0,  **kwargs):
        self.pin = pin
        self.freq = freq
        self.dma = dma
        self.invert = invert
        self.channel = channel

@DataClass(name="LedStrip")
class LedStrip:        
    def __init__(self, gpio, led_count, brightness = 255, strip_type=None, **kwargs):
        self.led_count = led_count
        self.brightness = brightness
        if isinstance(gpio, numbers.Number):
            gpio = GPIO.get_gpio(gpio)
        self.gpio = gpio.pin
        self.freq_hz = gpio.freq
        self.dma = gpio.dma
        self.invert = gpio.invert
        self.channel = gpio.channel

        self.strip_type = strip_type
        if isinstance(self.strip_type,str):
            self.strip_type = get_strip_type(self.strip_type)

        self.strip = PixelStrip(self.led_count, self.gpio, self.freq_hz,
                                       self.dma, self.invert, self.brightness,
                                       self.channel, self.strip_type)
        self.strip.begin()
        self.enabled = True
    
    def deinit(self):
        self.fill((0,0,0))
        self.show()
        self.strip._cleanup()

    def __enter__(self):
        if self.enabled == False:
            self.strip.begin()
            self.enabled = True
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.deinit()
        self.enabled = False

    def __getitem__(self, pos):
        if isinstance(pos, slice):
            return [((item >> 16) & 0xff, (item >> 8) & 0xff, item & 0xff) for item in self.strip.__getitem__(pos)]
        else:
            item = self.strip.__getitem__(pos)
            return ((item >> 16) & 0xff, (item >> 8) & 0xff, item & 0xff)

    def __setitem__(self, pos, value):
        """Set the 24-bit RGB color value at the provided position or slice of
        positions.
        """
        if isinstance(pos, slice):
            value = np.left_shift(value, (16,8,0))
            value = np.sum(value,1)
            v = 0
            for n in range(*pos.indices(self.strip.size)):
                ws.ws2811_led_set(self.strip._channel, n, int(value[v]))
                v += 1
        # Else assume the passed in value is a number to the position.
        else:
            value = np.left_shift(value, (16,8,0))
            value = np.sum(value)
            return ws.ws2811_led_set(self.strip._channel, pos, value)

    def __len__(self):
        return len(self.strip)
    
    def fill(self, value):
        value = np.left_shift(value, (16,8,0))
        value = np.sum(value)
        self.strip[:] = int(value)

    def show(self):
        self.strip.show()

    def setBrightness(self, brightness):
        self.strip.setBrightness(brightness)

    def activate(self, owner):
        pass

    def release(self, owner):
        pass

@DataClass(name="LedStripSection")
class LedStripSection:
    def build_slice(self, pos:slice):
        if pos.start is None:
            start = self.start
        else:
            start = self.start + pos.start * self.step
        
        if pos.stop is None:
            stop = self.stop
        else:
            stop = self.start + pos.stop * self.step
            if stop > self.stop:
                stop = self.stop 
        
        if pos.step is None:
            step = self.step
        else:
            step = pos.step * self.step
        return slice(start, stop, step)

    def __init__(self, led_strip, _slice=slice(None,None,None), **kwargs):
        self.led_strip = led_strip
        if isinstance(_slice, (tuple,list)):
            nleds = len(self.led_strip)
            self.start = self.try_value_from_arr(_slice, 0, 0, nleds)
            self.stop = self.try_value_from_arr(_slice, 1, nleds, nleds)
            self.step = self.try_value_from_arr(_slice, 2, 1, self.stop-self.start)

            self._slice = slice(self.start,self.stop,self.step)
            self.len = len(range(self.start, self.stop, self.step))
        else:
            self._slice = _slice
            self.start = _slice.start if _slice.start is not None else 0
            self.stop = _slice.stop if _slice.stop is not None else len(self.led_strip)
            self.step = _slice.step if _slice.step is not None else 1
            self.len = len(range(self.start, self.stop, self.step))

    def try_value_from_arr(self, _slice, index, default, nleds):
        if len(_slice) > index and _slice[index] is not None:
            val = _slice[index]
            if isinstance(val, float):
                val = val*nleds
            if val < 0:
                val = nleds + val
            return int(val)
        return default
    

    def __getitem__(self, pos):
        if not isinstance(pos, slice):
            pos = slice(pos, None, None)

        pos = self.build_slice(pos)

        return self.led_strip.__getitem__(pos)
    
    def __setitem__(self, pos, value):
        if not isinstance(pos, slice):
            pos = slice(pos, None, None)
        
        pos = self.build_slice(pos)

        return self.led_strip.__setitem__(pos, value)
    
    def __len__(self):
        return self.len
    
    def fill(self, value):
        self.led_strip[self._slice] = value
    
    def show(self):
        self.led_strip.show()

    def setBrightness(self, brightness):
        self.led_strip.setBrightness(brightness)

    def activate(self, owner):
        self.led_strip.activate(owner)

    def release(self, owner):
        self.led_strip.release(owner)

@DataClass(name="slice")
def build_slice(v = None, start = None, stop = None, step = None, **kwargs):
    if v is not None:
        v_len = len(v)
        if v_len > 2:
            step = v[2]
        if v_len > 1:
            stop = v[1]
        if v_len > 0:
            start = v[0]
    return slice(start, stop, step)

class GPIO:
    D10 = GpioInfo(10)
    D12 = GpioInfo(12)
    D13 = GpioInfo(13, channel= 1)
    D18 = GpioInfo(18)
    D19 = GpioInfo(13, channel= 1)
    D21 = GpioInfo(21)

    @DataClass(name="GPIO")
    def get_gpio(gpio, **kwargs):
        match gpio:
            case 10:
                return GPIO.D10
            case 12:
                return GPIO.D12
            case 13:
                return GPIO.D13
            case 18:
                return GPIO.D18
            case 19:
                return GPIO.D19
            case 21:
                return GPIO.D21
            case _:
                pass
        return None
