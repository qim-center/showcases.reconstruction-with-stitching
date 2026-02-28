import os
import time
from contextlib import contextmanager

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