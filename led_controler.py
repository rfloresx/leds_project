import RPi.GPIO as GPIO
import sys
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
import signal

class ThreadPool:
    class TaskInfo:
        def __init__(self, func, frame_time) -> None:
            self.func = func
            self.last_update = 0
            self.frame_time = frame_time
            self.next_update = datetime.datetime.now()
            self.refs_count = 0

        def is_ready(self):
            now = datetime.datetime.now()
            return self.next_update < now

        def run(self):
            self.last_update = datetime.datetime.now()
            self.func()
            self.next_update = self.last_update + datetime.timedelta(seconds=self.frame_time)
            return self.next_update

    def __init__(self, **kwargs):
        self.tasks = []
        self.thread= None
        self._stop = False
        self.lock = mp.Lock()

    def _run(self):
        self._stop = False
        while self._stop == False:
            now = datetime.datetime.now()
            next = None
            with self.lock:
                for task_info in self.tasks:
                    if next is None or next.next_update > task_info.next_update:
                        next = task_info
            if next is None:
                self._stop = True
                raise RuntimeError("Missing Task")
            if now < next.next_update:
                delta = (next.next_update - now).total_seconds()
                if delta > 0:
                    time.sleep(delta)
            next.run()

    def __start(self):
        if self.thread is None:
            self.thread = threading.Thread(target=self._run)
            self.thread.start()

    def get_task_info(self, task):
        with self.lock:
            for t in self.tasks:
                if t.func == task:
                    return t
        return None

    def start(self, task, frame_time):
        task_info = self.get_task_info(task)
        if task_info is None:
            task_info = ThreadPool.TaskInfo(task, frame_time)
            with self.lock:
                self.tasks.append(task_info)
        if frame_time < task_info.frame_time:
            task_info.frame_time = frame_time
        task_info.refs_count += 1
        self.__start()
        return task

    def stop(self, task):
        with self.lock:
            for t in self.tasks:
                if t.func == task:
                    t.refs_count -= 1
                    if  t.refs_count <= 0:
                        self.tasks.remove(t)                
                    break
        if len(self.tasks) == 0:
            self._stop = True
            if self.thread is not None:
                self.thread.join()
                self.thread = None
        
    def stop_all(self):
        if self.thread is not None:
            self._stop = True
            self.thread.join()
            self.thread = None

class LedController(led_strip.LedStrip):
    def __init__(self, refresh_rate, name = "", relay_pin = None, pool=None, **kwargs):
        super().__init__(**kwargs)
        self.lock = mp.Lock()
        self.pool = pool
        self.thread = None
        self._stop = True
        self.name = name
        self.refresh_rate = refresh_rate
        self.frame_time = 1/refresh_rate
        self.relay_pin = relay_pin
        if self.relay_pin is not None:
            GPIO.setup(self.relay_pin, GPIO.OUT)
        self.refs = set()
    
    def __run(self):
        with self.lock:
            led_strip.LedStrip.show(self)

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
            if self.relay_pin is not None:
                GPIO.output(self.relay_pin, GPIO.HIGH)
            self._stop = False
            if self.pool is None:
                self.thread = threading.Thread(target=self._run)
                self.thread.start()
            else:
                try:
                    _func = self.strip._leds.show
                except:
                    _func = self.__run
                self.thread = self.pool.start(_func, self.frame_time)
    def stop(self):
        self._stop = True
        if self.thread is not None:
            if self.pool is None:
                self.thread.join()
                self.thread = None
            else:
                self.pool.stop(self.thread)
    
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

class Simulator:
    def __init__(self,  enable, sim, name = "", refresh_rate = 15, **kwargs):
        self._stop = True
        self.thread = None
        self.enable = enable
        if not isinstance(sim, list):
            sim = [sim]
        self.simulations = sim

        self.name = name
        self.refresh_rate = refresh_rate
        self.frame_time = 1/refresh_rate

    def _run(self):
        self._stop = False

        while (self._stop == False):
            start = datetime.datetime.now()
            for s in self.simulations:
                s.update()

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
    "LedController":LedController,
    "ThreadPool":ThreadPool
}


class LedsController:
    CLASS_LIST = {
        **CLASS_LIST,
        **led_sim.CLASS_LIST, 
        **led_strip.CLASS_LIST,
        **palette.CLASS_LIST
    }

    def __signal(self, *args):
        self.kill_now = True

    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.__signal)
        signal.signal(signal.SIGTERM, self.__signal)

        self.name = ""
        self.info = ""

        self.refs = {}
        self.exit = False
        self.sims = []
        self.pools = []
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
        if isinstance(config, str):
            tokens = config.split(":")
            if len(tokens) > 1:
                if tokens[0] == "ref":
                    return self.get_instance(tokens[1])
            return config                
        elif isinstance(config, list):
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
            elif isinstance(obj, ThreadPool):
                self.pools.append(obj)

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
    config = None
    with open(args.configfile, 'r') as file:
        config = json.load(file)
    
    cont = LedsController()
    if config is not None:
        cont.load_config(config)
        cont.run()
    sys.exit(0)
