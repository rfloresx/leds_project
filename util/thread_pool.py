import datetime
import multiprocessing as mp
import threading
import time
from util.config import DataClass
@DataClass(name="ThreadPool")
class ThreadPool:
    class TaskInfo:
        def __init__(self, func, frame_time) -> None:
            self.func = func
            self.last_update = 0
            self.frame_time = frame_time
            self.next_update = datetime.datetime.now()

        def run(self):
            self.last_update = datetime.datetime.now()
            self.func()
            self.next_update = self.last_update + datetime.timedelta(seconds=self.frame_time)
            return self.next_update

        def __str__(self):
            return f"{self.func=} {self.frame_time=}"
    
        def __repr__(self):
            return str(self)
    
    def __init__(self, **kwargs):
        self.tasks = []
        self.thread= None
        self._stop = False
        self.lock = mp.Lock()

    def __run(self):
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
            self.thread = threading.Thread(target=self.__run)
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
        self.__start()
        return task

    def stop(self, task):
        with self.lock:
            for t in self.tasks:
                if t.func == task:
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
            self.tasks = []


class TimeThread:
    def __init__(self, _func, frame_time, pool=None, *kwargs):
        self._func = _func
        self.frame_time = frame_time
        self.pool = pool if pool is not None else ThreadPool()
        self.task_id = None

    def start(self):
        if self.task_id is None:
            self.task_id = self.pool.start(self._func, self.frame_time)
    
    def stop(self):
        if self.task_id is not None:
            self.pool.stop_all()
            self.task_id = None
