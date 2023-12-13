# Adafruit NeoPixel library port to the rpi_ws281x library.
# Author: Tony DiCola (tony@tonydicola.com), Jeremy Garff (jer@jers.net)
# Modified tu support multiple GPIO at the same time
import _rpi_ws281x as ws
import atexit

class RGBW(int):
    def __new__(self, r, g=None, b=None, w=None):
        if (g, b, w) == (None, None, None):
            return int.__new__(self, r)
        else:
            if w is None:
                w = 0
            return int.__new__(self, (w << 24) | (r << 16) | (g << 8) | b)

    @property
    def r(self):
        return (self >> 16) & 0xff

    @property
    def g(self):
        return (self >> 8) & 0xff

    @property
    def b(self):
        return (self) & 0xff

    @property
    def w(self):
        return (self >> 24) & 0xff


def Color(red, green, blue, white=0):
    """Convert the provided red, green, blue color to a 24-bit color value.
    Each color component should be a value 0-255 where 0 is the lowest intensity
    and 255 is the highest intensity.
    """
    return RGBW(red, green, blue, white)

class Ws2811:
    class ChannelInfo:
        def __init__(self, num, pin, invert, brightness, gamma, strip_type) -> None:
            self.num = num
            self.pin = pin
            self.invert = 0 if not invert else 1
            self.brightness = brightness
            self.gamma = gamma
            self.strip_type = strip_type

    __instance = None

    def instance():
        if Ws2811.__instance is None:
            Ws2811.__instance = Ws2811()
        return Ws2811.__instance
    
    def __str__(self):
        return f"{self.freq_hz}, {self.dma}, {self._leds}, {self.channels}"

    def __init__(self):
        self.freq_hz = None
        self.dma = None
        self._leds = None
        self.channels = [None, None]
        self.set_freq_dma()
    
    def set_freq_dma(self, freq_hz=800000, dma=10):
        if self.freq_hz is None and self.dma is None or self._leds is None:
            self.freq_hz = freq_hz
            self.dma = dma
        elif self.freq_hz != freq_hz or self.dma != dma:
            raise RuntimeError(f"Ws2811 already initialized with {self.freq_hz}:{self.dma}")

    def init(self):
        if self._leds is None:
            self._leds = ws.new_ws2811_t()
            atexit.register(self.__cleanup)
        else:
            ws.ws2811_fini(self._leds)

        # Initialize the controller
        ws.ws2811_t_freq_set(self._leds, self.freq_hz)
        ws.ws2811_t_dmanum_set(self._leds, self.dma)

        # Configure Channels
        for channum in range(2):
            self.__configure_channel(channum)
        
        resp = ws.ws2811_init(self._leds)
        if resp != 0:
            str_resp = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, str_resp))

    def __cleanup(self):
        # Clean up memory used by the library when not needed anymore.
        if self._leds is not None:
            ws.ws2811_fini(self._leds)
            ws.delete_ws2811_t(self._leds)
            self._leds = None

    def configure_channel(self, num, pin, channel = 0, invert=False, brightness=255, gamma=None, strip_type=None):
        if gamma is None:
            # Support gamma in place of strip_type for back-compat with
            # previous version of forked library
            if type(strip_type) is list and len(strip_type) == 256:
                gamma = strip_type
                strip_type = None
            else:
                gamma = list(range(256))

        if strip_type is None:
            strip_type = ws.WS2811_STRIP_RGB
        
        self.channels[channel] = Ws2811.ChannelInfo(num, pin, invert, brightness, gamma, strip_type)

    def get_channel(self, channel):
        return ws.ws2811_channel_get(self._leds, channel)
        
    def __configure_channel(self, channel):
        channel_info = self.channels[channel]
        _channel = ws.ws2811_channel_get(self._leds, channel)
        if channel_info != None:
            ws.ws2811_channel_t_gamma_set(_channel, channel_info.gamma)
            ws.ws2811_channel_t_count_set(_channel, channel_info.num)
            ws.ws2811_channel_t_gpionum_set(_channel, channel_info.pin)
            ws.ws2811_channel_t_invert_set(_channel, channel_info.invert)
            ws.ws2811_channel_t_brightness_set(_channel, channel_info.brightness)
            ws.ws2811_channel_t_strip_type_set(_channel, channel_info.strip_type)
        else:
            ws.ws2811_channel_t_count_set(_channel, 0)
            ws.ws2811_channel_t_gpionum_set(_channel, 0)
            ws.ws2811_channel_t_invert_set(_channel, 0)
            ws.ws2811_channel_t_brightness_set(_channel, 0)

    def begin(self):
        """Initialize library, must be called once before other functions are
        called.
        """
        self.init()
    
    def show(self):
        """Update the display with the data from the LED buffer."""
        resp = ws.ws2811_render(self._leds)
        if resp != 0:
            str_resp = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, str_resp))
    

class PixelStrip:
    def __init__(self, num, pin, freq_hz=800000, dma=10, invert=False,
            brightness=255, channel=0, strip_type=None, gamma=None):
        """Class to represent a SK6812/WS281x LED display.  Num should be the
        number of pixels in the display, and pin should be the GPIO pin connected
        to the display signal line (must be a PWM pin like 18!).  Optional
        parameters are freq, the frequency of the display signal in hertz (default
        800khz), dma, the DMA channel to use (default 10), invert, a boolean
        specifying if the signal line should be inverted (default False), and
        channel, the PWM channel to use (defaults to 0).
        """
        self._leds = Ws2811.instance()
        self._leds.set_freq_dma(freq_hz, dma)
        self._leds.configure_channel(num, pin, channel, invert, brightness, gamma, strip_type)
        self._leds.begin()

        self._channel = self._leds.get_channel(channel)
        self.size = num

    def __getitem__(self, pos):
        """Return the 24-bit RGB color value at the provided position or slice
        of positions.
        """
        # Handle if a slice of positions are passed in by grabbing all the values
        # and returning them in a list.
        if isinstance(pos, slice):
            return [ws.ws2811_led_get(self._channel, n) for n in range(*pos.indices(self.size))]
        # Else assume the passed in value is a number to the position.
        else:
            return ws.ws2811_led_get(self._channel, pos)

    def __setitem__(self, pos, value):
        """Set the 24-bit RGB color value at the provided position or slice of
        positions.
        """
        # Handle if a slice of positions are passed in by setting the appropriate
        # LED data values to the provided value.
        if isinstance(pos, slice):
            for n in range(*pos.indices(self.size)):
                ws.ws2811_led_set(self._channel, n, value)
        # Else assume the passed in value is a number to the position.
        else:
            return ws.ws2811_led_set(self._channel, pos, value)

    def __len__(self):
        return ws.ws2811_channel_t_count_get(self._channel)

    def setGamma(self, gamma):
        if type(gamma) is list and len(gamma) == 256:
            ws.ws2811_channel_t_gamma_set(self._channel, gamma)

    def begin(self):
        pass

    def show(self):
        self._leds.show()

    def setPixelColor(self, n, color):
        """Set LED at position n to the provided 24-bit color value (in RGB order).
        """
        self[n] = color

    def setPixelColorRGB(self, n, red, green, blue, white=0):
        """Set LED at position n to the provided red, green, and blue color.
        Each color component should be a value from 0 to 255 (where 0 is the
        lowest intensity and 255 is the highest intensity).
        """
        self.setPixelColor(n, Color(red, green, blue, white))

    def getBrightness(self):
        return ws.ws2811_channel_t_brightness_get(self._channel)

    def setBrightness(self, brightness):
        """Scale each LED in the buffer by the provided brightness.  A brightness
        of 0 is the darkest and 255 is the brightest.
        """
        ws.ws2811_channel_t_brightness_set(self._channel, brightness)

    def getPixels(self):
        """Return an object which allows access to the LED display data as if
        it were a sequence of 24-bit RGB values.
        """
        return self[:]

    def numPixels(self):
        """Return the number of pixels in the display."""
        return len(self)

    def getPixelColor(self, n):
        """Get the 24-bit RGB color value for the LED at position n."""
        return self[n]

    def getPixelColorRGB(self, n):
        return RGBW(self[n])

    def getPixelColorRGBW(self, n):
        return RGBW(self[n])

# Shim for back-compatibility
class Adafruit_NeoPixel(PixelStrip):
    pass
