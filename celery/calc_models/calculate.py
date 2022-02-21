"""main entry point for starting a big calculation that takes time"""
import time
from joblib import Parallel, delayed, parallel_backend, wrap_non_picklable_objects
from multiprocessing.pool import Pool
from multiprocessing import current_process
from functools import partial

# just a dummy function, adding two numbers, after waiting _duration_ seconds.
# this would typically be loading a model (from e.g. ML Flow), running train/fit/predict
def slow_sum(duration, a, b):
    return _calculate('add', a, b, duration)


def parallel_operations(duration, a, b):
    operations = ['add', 'sub', 'mul', 'div', 'pow', 'mod', 'fdiv']

    # Different ways of doing parallel computing - that is tested and works:
    # joblib out of the box:
    # r = Parallel(n_jobs=-1)(delayed(_calculate)(o, a, b, duration) for o in operations)

    # joblib and threading:
    # with parallel_backend('threading'):
    #    r = Parallel(n_jobs=-1)(delayed(_calculate)(o, a, b, duration) for o in operations)

    # Using multiprocessing pool:
    with Pool() as p:
        r = p.map(partial(_calculate, duration=duration, a=a, b=b), operations)

    return str({i[0]:i[1] for i in zip(operations, r)})

# This is to make joblib loky process work,
# if not you'll get a message saying that arguments cannot be serialized.
# see: https://joblib.readthedocs.io/en/latest/auto_examples/serialization_and_wrappers.html
@wrap_non_picklable_objects
def _calculate(operation, a, b, duration):

    time.sleep(duration)
    if operation=='add':
        res = a + b
    elif operation=='sub':
        res = a - b
    elif operation=='mul':
        res = a * b
    elif operation=='div':
        res = a / b
    elif operation=='pow':
        res = a ** b
    elif operation=='mod':
        res = a % b
    elif operation=='fdiv':
        res = a // b
    else:
        res = float(str(a) + str(b))
    return res


if __name__=="__main__":
    print(parallel_operations(4, 4, 5))