import logging
from systemd.journal import JournalHandler
import sys
import traceback

class Logger(object):
    __instance = None
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Logger,cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):      
        if(self.__initialized): return
        self.log = logging.getLogger('led_conn')
        self.log.addHandler(JournalHandler())
        self.log.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)
        self.__initialized = True

def debug(msg, *args, **kwargs):
    Logger().log.debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    Logger().log.debug(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    if isinstance(msg, Exception):
        Logger().log.error(traceback.format_exc())
    Logger().log.error(msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
    Logger().log.exception(msg, *args, **kwargs)