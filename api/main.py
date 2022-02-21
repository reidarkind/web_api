from __future__ import absolute_import
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from celery.exceptions import TimeoutError

from data_model import InData, OutResponse
from worker import celery_app

app = FastAPI()


@app.post("/start_simple_task", response_model=OutResponse)
async def start_simple_task(data:InData, request: Request):
    """Endpoint for starting a simple calculation

    Parameters
    ----------
    data : InData
        Containing indata, based on scheme defined by pydantic object InData

    Returns
    -------
    OutResponse
        Data on scheme defined by pydantic object OutResponse
    """
    # set task name and start task
    # todo: could be better to put the task names in environment variables,
    # then use those to ensure task names are the same here and in celery.tasks
    task_name = "start_simple_task"
    task = _start_task(data, task_name)

    # get results/status and organize response data
    response = _get_task_status(task, _get_url(request))
    return response


@app.post("/start_parallel_task", response_model=OutResponse)
async def start_parallel_task(data:InData, request: Request):
    """Endpoint for starting a parallel calculation

    Parameters
    ----------
    data : InData
        Containing indata, based on scheme defined by pydantic object InData

    Returns
    -------
    OutResponse
        Data on scheme defined by pydantic object OutResponse
    """
    # set task name and start task
    task_name = "start_parallel_task"
    task = _start_task(data, task_name)

    # get results/status and organize response data
    response = _get_task_status(task, _get_url(request))
    return response


@app.get("/status/{id}")
async def get_status(id:str, request: Request):
    """Returns status and results for a given task

    Parameters
    ----------
    id : str
        The id of the task. id is return by the start_slow_sum POST.

    Returns
    -------
    OutResponse
        Data on scheme defined by pydantic object OutResponse
    """
    # get results/status and organize response data
    task = celery_app.AsyncResult(id)
    return _get_task_status(task, _get_url(request))

# response_model_exclude_unset=True drops unset keys in the response object,
# instead of leaving them with None value (since all keys are optional with None = None in the data model)
@app.get("/result/{id}", response_model=OutResponse, response_model_exclude_unset=True)
async def get_result(id:str):
    """Fetching the results only for a given task id.

    Parameters
    ----------
    id : str
        The id of the task. id is return by the start_slow_sum POST.

    Returns
    -------
    JSONResponse(dict)
        Json containing the result if job has finished or
        status of the task if task has not finished or failed.
    """
    task = celery_app.AsyncResult(id)
    status = task.state
    if status.lower() == 'success':
        result = task.result
        return OutResponse(result=result)
    else:
        return OutResponse(result=status)


def _get_url(request):
    """Function to show how the request object can be used to fetch info about the request (or client)

    Parameters
    ----------
    request : startlette.requests.Request
        The request object received in the GET or POST

    Returns
    -------
    str
        The first part of the url, Protocol, host, port (if given),
        Example: http://localhost:80/
    """
    host = "/".join(str(request.url).split("/")[0:3]) + "/"

    return host


def _start_task(data:InData, task_name):
    """Helper method to start a celery task, based on the input data.

    Parameters
    ----------
    data : InData
        object containing the data received in the POST request
    task_name : str
        name of the task to start (defined in the ../celery/tasks.py file)

    Returns
    -------
    celery.AsyncResult
        The task object that is created
    """
    # get data from data body of the POST
    duration = data.duration
    a = data.a
    b = data.b

    # send task with input data via broker to backend (celery_app is already set up in worker.py)
    task = celery_app.send_task(task_name, args=[duration, a, b])

    # fetch results, either wait til finished (if data.wait==None) or
    # wait for data.wait seconds to return results
    if data.wait is not None:
        # if wait is given, we will wait maximum that amount of seconds to retreive the results
        try:
            celery_app.AsyncResult(task.id).get(data.wait)
        except TimeoutError:
            # goes here if no result were fetch within timout (=data.wait)
            pass
    else:
        celery_app.AsyncResult(task.id).get()
    return task


def _get_task_status(task, url):
    """Organizes task result into a respons object

    Parameters
    ----------
    task : celery.AsyncResult
        The task for which one wants to organize the status/results data.

    Returns
    -------
    OutResponse
        Data on scheme defined by pydantic object OutResponse
    """

    status = task.state
    if status.lower() == 'success':
        response = OutResponse(
            status = task.state,
            result = task.result,
            task_id = task.id,
            full_traceback = None,
            url=f"{url}status/{task.id}"
        )
    elif status.lower() == 'failure':
        #TODO: test this
        res = json.loads(task.backend.get(task.backend.get_key_for_task(task.id)).decode('utf-8'))
        #del res['children']
        #del res['traceback']
        response = OutResponse(
            status = task.state,
            result = None,
            task_id = task.id,
            full_traceback = res,
            url=f"{url}status/{task.id}"
        )

    else:
        response = OutResponse(
            status = task.state,
            result = task.info,
            task_id = task.id,
            full_traceback = None,
            url=f"{url}status/{task.id}"
        )
    return response

