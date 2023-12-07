import logging
from systemd.journal import JournalHandler

# log = logging.getLogger('led_conn')
# log.addHandler(JournalHandler())
# log.setLevel(logging.INFO)

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
        self.log.setLevel(logging.INFO)
        self.__initialized = True

def debug(msg, *args, **kwargs):
    Logger().log.debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    Logger().log.debug(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    Logger().log.error(msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
    Logger().log.exception(msg, *args, **kwargs)