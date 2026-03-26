import os
import time
from contextlib import contextmanager, ContextDecorator
import psutil
import threading

import numpy as np

if os.getenv('MEMORY_PROFILER'):
    from memory_profiler import profile
else:
    def profile(func):
        return func

@contextmanager
def timed(label: str):
    t0 = time.perf_counter()
    yield
    dt = time.perf_counter() - t0
    print(f"  {label:>20}: {dt:.2f} s")


def to_uint8(x, bounds=(1, 99)):
    lo, hi = np.percentile(x, bounds)
    x = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return (x * 255).astype(np.uint8)

class ProcessSampler:
    def __init__(self, interval=0.2):
        self.interval = interval
        self._stop = threading.Event()
        self._thread = None
        self.pid = os.getpid()

        self.max_parent_rss = 0
        self.max_tree_rss = 0
        self.max_children = 0
        self.max_threads = 0

    def _sample_once(self):
        try:
            parent = psutil.Process(self.pid)
        except psutil.Error:
            return

        try:
            parent_rss = parent.memory_info().rss
            threads = parent.num_threads()
            children = parent.children(recursive=True)
        except psutil.Error:
            return

        tree_rss = parent_rss
        live_children = []

        for c in children:
            try:
                tree_rss += c.memory_info().rss
                live_children.append(c)
            except psutil.Error:
                pass

        self.max_parent_rss = max(self.max_parent_rss, parent_rss)
        self.max_tree_rss = max(self.max_tree_rss, tree_rss)
        self.max_children = max(self.max_children, len(live_children))
        self.max_threads = max(self.max_threads, threads)

    def _run(self):
        while not self._stop.is_set():
            self._sample_once()
            time.sleep(self.interval)

    def start(self):
        self._sample_once()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
        self._sample_once()

    def report(self, tag):
        print(
            f"[MONITOR] {tag} | "
            f"max_parent_rss={self.max_parent_rss / 1024**3:.2f} GiB "
            f"max_tree_rss={self.max_tree_rss / 1024**3:.2f} GiB "
            f"max_children={self.max_children} "
            f"max_threads={self.max_threads}",
            # file=sys.stderr,
            flush=True,
        )

class ProcessMonitor(ContextDecorator):
    def __init__(self, tag, interval=1.0, report=True, include_time=True):
        self.tag = tag
        self.interval = interval
        self.report_enabled = report
        self.include_time = include_time
        self._pmon = None
        self._t0 = None

    def __enter__(self):
        self._pmon = ProcessSampler(interval=self.interval)
        self._t0 = time.time()
        self._pmon.start()
        return self

    def __exit__(self, *exc):
        self._pmon.stop()
        dt = time.time() - self._t0

        if self.report_enabled:
            if self.include_time:
                print(f"{self.tag}: {dt:.2f} s", flush=True)
            self._pmon.report(self.tag)

        return False

class NoMonitor(ContextDecorator):
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


if os.getenv("PROC_MONITOR"):
    monitor = ProcessMonitor
else:
    monitor = NoMonitor