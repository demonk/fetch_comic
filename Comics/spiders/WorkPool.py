#!/usr/bin/python
# -*- coding:utf-8 -*-

import Queue
import threading
import time
import traceback

import random
from time import sleep

from blessings import Terminal

from progressive.bar import Bar
from progressive.tree import ProgressTree, Value, BarDescriptor

__DEFAULT_NUM__ = 5


class WorkPool:
    def __init__(self, worker_num=__DEFAULT_NUM__):
        self.workers = []
        self.leaf_values = [Value(0) for i in range(worker_num)]

        for i in range(0, worker_num):
            self.workers.append(Worker(i))

    def selectWorker(self):
        worker = None
        for w in self.workers:
            if worker == None or w.task_num() < worker.task_num():
                worker = w

        return worker

    def add_task(self, func, *args):
        availableWorker = self.selectWorker()
        if availableWorker:
            availableWorker.add_task(func, args)

    def wait(self):
        for worker in self.workers:
            worker.join()


class Worker(threading.Thread):
    def __init__(self, id):
        threading.Thread.__init__(self)
        self.id = id
        self.work_queue = Queue.Queue()
        self.size = 0
        self.running = False

    def getId(self):
        return self.id

    def add_task(self, func, args):  # 由于这个args是从外边*args传进来的，不需要再取地址,否则多个参数会被打包成一个对象
        self.work_queue.put((func, args))
        self.size += 1

        if not self.running:
            self.start()

    def task_num(self):
        return self.size

    def isRunning(self):
        return self.running

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            if 0 == self.task_num():
                continue

            try:
                func, args = self.work_queue.get(block=False)
                func(*args)  # 重新取值，避免直接函数调用时参数个数匹配不上
                self.size -= 1
                self.work_queue.task_done()
            except Exception, e:
                traceback.print_exc()
                break
