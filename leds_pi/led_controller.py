
import RPi.GPIO as GPIO
import leds_pi.led_strip as led_strip
import multiprocessing as mp
import util.thread_pool as thread_pool
from util.config import DataClass

@DataClass(name="LedController")
class LedController(led_strip.LedStrip):
    def __init__(self, refresh_rate, name = "", relay_pin = None, pool=None, **kwargs):
        super().__init__(**kwargs)
        self.lock = mp.Lock()
        self.pool = pool
        self.name = name
        self.refresh_rate = refresh_rate
        self.frame_time = 1/refresh_rate
        self.thread = thread_pool.TimeThread(self.__run, self.frame_time, pool=self.pool)
        self.relay_pin = relay_pin
        if self.relay_pin is not None:
            GPIO.setup(self.relay_pin, GPIO.OUT)
        self.refs = set()

    def deinit(self):
        if self.relay_pin is not None:
            GPIO.output(self.relay_pin, GPIO.LOW)
        super().deinit()

    def __run(self):
        with self.lock:
            led_strip.LedStrip.show(self)

    def start(self):
        if self.relay_pin is not None:
            GPIO.output(self.relay_pin, GPIO.HIGH)
        self.thread.start()

    def stop(self):
        self.thread.stop()
    
    def __getitem__(self, pos):
        with self.lock:
            return super().__getitem__(pos)
    
    def __setitem__(self, pos, value):        
        with self.lock:
            return super().__setitem__(pos, value)
    
    def __len__(self):
        with self.lock:
            return len(self.strip)
    
    def fill(self, value):
        with self.lock:
            super().fill(value)
    
    def show(self):
        pass

    def setBrightness(self, brightness):
        with self.lock:
            return super().setBrightness(brightness)

    def activate(self, owner):
        self.refs.add(owner)
        self.start()

    def release(self, owner):
        self.refs.remove(owner)
        if len(self.refs) == 0:
            self.stop()

