import RPi.GPIO as GPIO

import led_sim
import palette

import argparse
import threading
import multiprocessing as mp
import json
import time
import datetime

import logger

import led_strip

class LedController(led_strip.LedStrip):
    def __init__(self, refresh_rate, name = "", relay_pin = None, **kwargs):
        super().__init__(**kwargs)
        self.lock = mp.Lock()
        self.thread = None
        self._stop = True
        self.name = name
        self.refresh_rate = refresh_rate
        self.frame_time = 1/refresh_rate
        self.relay_pin = relay_pin
        if self.relay_pin is not None:
            GPIO.setup(self.relay_pin, GPIO.OUT)
        self.refs = set()
        print("__init__")
    
    def _run(self):
        while (self._stop == False):
            start = datetime.datetime.now()
            with self.lock:
                led_strip.LedStrip.show(self)
            end = datetime.datetime.now()
            delta = (end - start).total_seconds()
            sleep_time = self.frame_time - delta
            if sleep_time > 0:
                time.sleep(sleep_time)

    def start(self):
        if self.thread is None:
            self._stop = False
            self.thread = threading.Thread(target=self._run)
            self.thread.start()

    def stop(self):
        self._stop = True
        if self.thread is not None:
            self.thread.join()
            self.thread = None
    
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
        print("activate")
        self.refs.add(owner)
        self.start()

    def release(self, owner):
        print("release")
        self.refs.remove(owner)
        if len(self.refs) == 0:
            self.stop()

class Simulator:
    def __init__(self,  enable, sim, name = "", refresh_rate = 15, **kwargs):
        self._stop = True
        self.thread = None
        self.enable = enable
        self.sim = sim
        self.name = name
        self.refresh_rate = refresh_rate
        self.frame_time = 1/refresh_rate

    def _run(self):
        self._stop = False

        while (self._stop == False):
            start = datetime.datetime.now()
            self.sim.update()
            end = datetime.datetime.now()
            delta = (end - start).total_seconds()
            sleep_time = self.frame_time - delta
            if sleep_time > 0:
                time.sleep(sleep_time)


    def start(self):
        if self.thread == None:
            logger.info(f"Starting {self.name}...")
            self.thread = threading.Thread(target = self._run)
            self.thread.start()

    def stop(self):
        logger.info(f"stoping {self.name}...")
        self._stop = True
        if self.thread is not None:
            self.thread.join()
            self.thread = None

CLASS_LIST = {
    "Simulator":Simulator,
    "LedController":LedController
}


class LedsController:
    CLASS_LIST = {
        **CLASS_LIST,
        **led_sim.CLASS_LIST, 
        **led_strip.CLASS_LIST,
        **palette.CLASS_LIST
    }

    def __init__(self):
        self.name = ""
        self.info = ""

        self.refs = {}
        self.exit = False
        self.sims = []
        self.class_list = {
            **LedsController.CLASS_LIST,
            "ref" : self.get_instance
        }
        GPIO.setmode(GPIO.BCM)
        
    def get_instance(self, name, **kwargs):
        if name in self.refs:
            return self.refs[name]
        return None

    def load_class(self, config):
        cls_name = config["class"]
        name = config.get("name",None)
    
        for k in config:
            config[k] = self.proces_config(config[k])

        obj = None
        if cls_name in self.class_list:
            obj = self.class_list[cls_name](**config)

        ret_val = config
        if obj is not None:
            if name is not None:
                obj.name = name
            ret_val = obj
        if name is not None:
            self.refs[name] = ret_val
        return ret_val

    def proces_config(self, config):
        if isinstance(config, list):
            tmp = config
            config = []
            for n in tmp:
                config.append(self.proces_config(n))
        elif isinstance(config, dict):
            if "class" in config:
                return self.load_class(config)
            else:
                for k in config:
                    config[k] = self.proces_config(config[k])
        return config

    def load_config(self, config):
        for item in config["config"]:
            obj = self.load_class(item)
            if isinstance(obj, Simulator):
                self.sims.append(obj)

        # self.pixels = {}
        # for pixels in config["NeoPixels"]:
        #     obj = self.load_class(pixels)
        #     if obj.name is not None:
        #         self.pixels[obj.name] = obj
        # self.sims = []
        # for sim in config["Simulations"]:
        #     obj = self.load_class(sim)
        #     self.sims.append(obj)
        #     # if obj.name is not None:
    
    def run(self):
        print("RUN")
        self.exit = False
        
        for sim in self.sims:
            if sim.enable == True:
                sim.start()
        
        while self.exit == False:
            try:
                time.sleep(1)
            except:
                logger.exception("Err")
                self.exit = True
        
        for sim in self.sims:
            sim.stop()
        
    

        


g_parser = argparse.ArgumentParser(prog='LED Controller')
g_parser.add_argument('-f', '--configfile', type=str, required=True)
g_parser.add_argument('-d', '--daemon', action='store_true')

if __name__ == "__main__":
    args = g_parser.parse_args()
    config = None
    with open(args.configfile, 'r') as file:
        config = json.load(file)
    
    cont = LedsController()
    if config is not None:
        cont.load_config(config)
        cont.run()

