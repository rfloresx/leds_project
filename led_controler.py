import RPi.GPIO as GPIO
import sys

import argparse
import json
import time
import signal

# import util 
# import leds_pi
# import effects
# import configs

import util.logger as logger
import util.thread_pool as thread_pool
import util.config as config

@config.DataClass(name="EffectsUpdater")
class EffectsUpdater:
    def __init__(self,  enable, effects, name = "", refresh_rate = 15, **kwargs):
        self._stop = True
        self.thread = None
        self.enable = enable
        if not isinstance(effects, list):
            effects = [effects]
        self.effects = effects

        self.name = name
        self.refresh_rate = refresh_rate
        self.frame_time = 1/refresh_rate
        self.thread = thread_pool.TimeThread(self._run, self.frame_time)

    def _run(self):
        for s in self.effects:
            s.update()

    def start(self):
        logger.info(f"Starting {self.name}...")
        self.thread.start()

    def stop(self):
        logger.info(f"stoping {self.name}...")
        self.thread.stop()

class LedsController:
    def __signal(self, *args):
        self.kill_now = True

    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.__signal)
        signal.signal(signal.SIGTERM, self.__signal)
        GPIO.setmode(GPIO.BCM)
        self.sims = []
        self.pools = []
    
    def load_config(self, json_obj):
        conf = config.Config.load_from_json(json_obj)
        objs = config.Config.get_all_objects()

        for item in objs:
            if isinstance(item, EffectsUpdater):
                self.sims.append(item)
            elif isinstance(item, thread_pool.ThreadPool):
                self.pools.append(item)
    
    def run(self):
        self.exit = False
        
        for sim in self.sims:
            if sim.enable == True:
                sim.start()
        
        while self.exit == False and self.kill_now == False:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Exit")
                self.exit = True
        
        for sim in self.sims:
            sim.stop()
        
        for pool in self.pools:
            pool.stop_all()


g_parser = argparse.ArgumentParser(prog='LED Controller')
g_parser.add_argument('-f', '--configfile', type=str, required=True)
g_parser.add_argument('-d', '--daemon', action='store_true')

if __name__ == "__main__":
    args = g_parser.parse_args()
    conf = None
    with open(args.configfile, 'r') as file:
        conf = json.load(file)
    cont = LedsController()

    if conf is not None:
        cont.load_config(conf)
        cont.run()
    sys.exit(0)
