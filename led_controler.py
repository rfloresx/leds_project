import sys
import board
import neopixel
import numpy as np
import RPi.GPIO as GPIO

import led_sim
import palette

import argparse
import threading
import multiprocessing as mp
import json
import types
import time

import logger

def get_pin(id, **kwargs):
    match id:
        case 10:
            return board.D10
        case 12:
            return board.D12
        case 18:
            return board.D18
        case 21:
            return board.D21
        case _:
            pass
    return None

class Simulator:
    def __init__(self,  enable, sim, **kwargs):
        self._stop = True
        self.thread = None
        self.enable = enable
        self.sim = sim

    def _run(self):
        self._stop = False

        while (self._stop == False):
            self.sim.update()

    def start(self):
        if self.thread == None:
            logger.info("Starting Service")
            self.thread = threading.Thread(target = self._run)
            self.thread.start()

    def stop(self):
        logger.info("stoping Service")
        self._stop = True
        if self.thread is not None:
            self.thread.join()
            self.thread = None

class Message:
    def __init__(self, msg, data):
        self.msg = msg
        self.data = data

    def from_json(txt):
        return json.loads(txt, object_hook=lambda d: types.SimpleNamespace(**d))
  
    def to_json(self):
        return json.dumps(self)

class LedControllerService:
    def __init__(self, authkey):
        self.address = ('localhost', 6000)
        self.authkey = authkey
        self.exit = False

    def start(self):
        self.exit = False
        self.listener = mp.connection.Listener(self.address, authkey=authkey)

        while self.exit == False:
            with self.listener.accept() as conn:
                logger.info(f"Connection accepted from {self.listener.last_accepted}")
                while True:
                    try:
                        msg = conn.recv()
                        rc = self.on_message(msg)
                        if rc != 0:
                            conn.close()
                    except EOFError:
                        logger.error(f"Connection lost")
                        break
        self.listener.close()

    def on_message(self, msg):
        match msg.cmd:
            case 'close':
                return -1
            case 'stop':
                self.exit = True
                return -1
            case _:
                logger.info(f"{msg}")
        return 0

class LedControllerClient:
    def __init__(self, authkey):
        self.address = ('localhost', 6000)
        self.authkey = authkey
    
    def start(self):
        self.client = mp.connection.Client(self.address, authkey= self.authkey)
        while True:
            pass


class LedsController:
    CLS_LIST = {
        "Simulator":Simulator,
        "NeoPixelController" : led_sim.NeoPixelController,
        "FireSim" : led_sim.FireSim,
        "RollSim" : led_sim.RollSim,
        "FadeSim" : led_sim.FadeSim,
        "SparkSim" : led_sim.SparkSim,
        "Palette" : palette.Palette,
        "PIN" : get_pin,
    }

    def __init__(self):
        self.pixels = {}
        self.exit = False

    def get_instance(self, name):
        if name in self.pixels:
            return self.pixels[name]
        return None

    def load_class(self, config):
        cls_name = config["class"]
        name = config.get("name",None)
    
        for k in config:
            config[k] = self.proces_config(config[k])

        obj = None
        if "ref" == cls_name:
            return self.get_instance(name)
        elif cls_name in LedsController.CLS_LIST:
            obj = LedsController.CLS_LIST[cls_name](**config)

        if obj is not None:
            obj.name = name
            return obj
        else:
            return config

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
        self.pixels = {}
        for pixels in config["NeoPixels"]:
            obj = self.load_class(pixels)
            if obj.name is not None:
                self.pixels[obj.name] = obj
        self.sims = []
        for sim in config["Simulations"]:
            obj = self.load_class(sim)
            self.sims.append(obj)
            # if obj.name is not None:
    
    def run(self):
        self.exit = False
        GPIO.setmode(GPIO.BCM)
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

