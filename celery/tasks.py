import os

from celery import Celery
from celery.signals import worker_process_init
from multiprocessing import current_process

# internal imports
from calc_models.calculate import slow_sum, parallel_operations
from worker import celery_app


# overwrite config, so that multiprocessing jobs work (with risk of oversubscribtion)
# without this method we will get this warning (or similair - depending on parallel backend)
# and n_jobs are set to 1:
# UserWarning: Loky-backed parallel loops cannot be called in a multiprocessing, setting n_jobs=1

@worker_process_init.connect
def fix_multiprocessing(**kwargs):
    current_process()._config['daemon'] = False

# The wrapping registers a task to the celery application
# by using bind=True we get the task element it self as first argument, just as a bound class method
@celery_app.task(bind=True, name="start_simple_task")
def start_simple_task(self, duration, a, b):
    res = slow_sum(duration, a, b)
    # Here one could trigger a webhook with a request provided by the user of the API,
    # so that the user then automatically could fetch the result. Something like
    # import requests
    # url = [the webhook provided as input to this method]
    # obj = {id: self.request.id}
    # requests.post(url, data=obj)
    print(f"Task with id {self.request.id} has finished. Here we could trigger a webhook.")
    return res

# if binding is not needed, just omit it..
@celery_app.task(name="start_parallel_task")
def start_parallel_task(duration, a, b):
    return parallel_operations(duration, a, b)
