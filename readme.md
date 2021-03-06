# WEB API with FastAPI, Celery and Redis

This project demonstrates how FastAPI, Celery, Redis can be used to put to gether services for deploying
heavy calculations.

## tldr;

Start services with:

```console
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d --no-deps
```

or install **make** (Tip: use git bash) and run

```console
make buildup
```

from the root folder of this project.


This will start 4 services;

* the webapi - based on FastAPI
* the broker - based on celery
* backend - based on redis, and
* monitoring of backend - based on flower

After all services is up, you can go to

* [http://localhost:8080/docs]() to read the automatic generated Swagger documentation and make requests to the
REST api endpoints
* [http://localhost:5555]() to monitor the backend, pending tasks etc.
* Do a request by using curl (tip: open your Git Bash - there you have curl) with:

```bash
curl -X 'POST' \
  'http://localhost/start_simple_task' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "duration": 0,
  "a": 1,
  "b": 1,
  "wait": 1
}'
```

## Virtual environment - conda

In the root of the project there is a environment file (`environment.yml`). To create a conda virtual environment you only have to write

```bash
conda evn create
```

to have the virtual environement set up. Then activate with:

```bash
conda activate py310_gen_api
```


## Project folders and files

```
gen_api
│   .env                                     --> containing environment variables
│   docker-compose.dev.yml                   --> override for development environment
│   docker-compose.prod.yml                  --> override production environment
│   docker-compose.yml                       --> common docker compose for dev and prod environment
│   DockerfileCelery                         --> Dockerfile used for Celery and Flower services
│   DockerfileRedis                          --> Dockerfile used for Redis service
│   DockerfileWebapi                         --> Dockerfile used for Web API service
│   makefile                                 --> Makefile to make it easier to use docker-compose
│   readme.md                                --> This file
│   requirementsCelery.txt                   --> Python requirements used in Celery dockerfile
│   requirementsCelerydev.txt                --> Additional Python requirements used in development for Celery dockerfile (auto-reload on code change.)
│   requirementsWebapi.txt                   --> Python requirements used in Web api docker file
│   __init__.py
│
├───api
│   data_model.py                            --> Pydandic data models, defining input and output schemes for the web api
│   main.py                                  --> End points of the web api
│   worker.py                                --> Set up of the celery worker, with info on broker and backend from environment variables, defined in .env
│   __init__.py
│
├───celery
│   │   tasks.py                             --> definition of celery tasks, triggering different calculations in ./calc_models
│   │   worker.py                            --> hardlink to ../api/.worker.py
│   │   __init__.py
│   │
│   └───calc_models
│       calculate.py                         --> The calculation "models" are developed here.
│       __init__.py
│
├───redis
│       init.sh                              --> changed redis config (memory handling) and startup of redis
│       redis.conf                           --> (unchanged from default) redis config file.
│       sysctl.conf                          --> redis config, memory handling
│
└───_misc
        api architecture.pptx                --> Powerpoint used to create the Services.PNG
        Endpoints.PNG                        --> image embedded in this readme.md
        Services.PNG                         --> image embedded in this readme.md
```


## Architecture

The following picture describes the flow between services:

![Architecture](./_misc/Services.PNG)

## FastAPI - the endpoints

You can open (in dev) `http://localhost:8080/docs` to see what end points are available and their full documentation, with possibility to try out the end points. I'll look something like this:

![Endpoints](./_misc/Endpoints.PNG)

This project contains 4 end-points:

* __POST__ **/start_simple_task** Starts a task that is calculated without any multiprocessing. Returns full response scheme:
* __POST__ **/start_parallel_task** Starts a task that calculates several relationships between two numbers, _a_ and _b_, in parallel (multiprocessing)
* __GET__ **/status/{id}** Returns full response scheme for a specific id
* __GET__ **/result/{id}** Returns only either result if success or status on job if not, from the response scheme.

### Full response scheme

```json
{
  "status": "string",
  "result": "string",
  "task_id": "string",
  "full_traceback": "string",
  "url": "string"
}
```

### Input scheme

The two __POST__ endpoints get data through this scheme:

```json
{
  "duration": 0,
  "a": 0,
  "b": 0,
  "wait": 0
}
```
To mimic a heavy calculation the `duration` argument defines how long the calculation should take (using `time.sleep(duration)`).
The arguments _a_ and _b_ are two numbers that are added in the simple task. The parallel task calculates 7 relationships:

* add: a+b
* sub: a-b
* mul: a*b
* div: a/b
* pow: a**b
* mod: a%b
* fdiv: a//b

Each calculation takes `duration` seconds to do.

The argument `wait` defines how long the web api should wait before it request status from the broker and return it as a respons to the request.

## Make

To make things a bit easier, using docker-compose the main functions are wrapped in a makefile:

```console
$ make help
usage: make target [arg=arg, *]

targets:
          help: this text
          build: build image(s), argument c and e available
          buildup: build image(s), create and start container(s), argument c, d, e available
          up: start container(s), argument c, d, e available
          start: start container(s), argument c and e available
          down: stop and remove container(s), argument c, e available
          stop: stop container(s), argument c, e available
          restart: same as make stop & make start in sequenze, argument c, d and e available
          logs: return logs of container(s), argument c and e available
          logs-api: return logs for api container, argument e available
          ps: list containers
          login-api: start interactive prompt for container api, argument e available
          login-celery_worker: start interactive prompt for container celery_worker, argument e available
          login-redis: start interactive prompt for container redis, argument e available
          Tip: leave login with command "exit" or ctrl-D

arguments:
          c: container name(s), usage: c=container_name or c="container1 container2 ..."
          d: run command detached or not, default is detatched, usage: d=false
             Detached mode: Run containers in the background
          e: which docker-compose environment file to use, default is docker-compose.dev.yml
             usage: e=prod to use docker-compose.prod.yml"

EXAMPLE:
          make buildup c="redis flower" d=false e=prod
          will build, create and start the container (in "undetatched mode") for redis and flower,
          using the docker-compose.yml with overrides from docker-compose.prod.yml
```

## Celery - Multiprocessing

The main goal with this project was to test whether or not one could trigger multiprocess tasks from _one_ celery task.
It appear to work, but not straight out of the box:

Firstly, it looks like the tasks are ran as deamons, and apparantly deamonic processes are not allowed to have children. Hence, the code:

```python
@worker_process_init.connect
def fix_multiprocessing(**kwargs):
    current_process()._config['daemon'] = False
```

Secondly, using the nativ serialization (pickling) of arguments does not work. Hence, the methods that are called as `delayed` methods need to be wrapped with:

```python
from joblib import wrap_non_picklable_objects

...

@wrap_non_picklable_objects
```

See [joblib documentation](https://joblib.readthedocs.io/en/latest/auto_examples/serialization_and_wrappers.html) for more info on the topic.

Two different methods (process and thread) seems to work, using joblib:

```python
    r = Parallel(n_jobs=-1)(delayed(_calculate)(o, a, b, duration) for o in operations)
```

or

```python
    with parallel_backend('threading'):
       r = Parallel(n_jobs=-1)(delayed(_calculate)(o, a, b, duration) for o in operations)
```

Another approach is using a Pool object:

```python
    with Pool() as p:
        r = p.map(partial(_calculate, duration=duration, a=a, b=b), operations)
```

But mind you! Import from 'billiard' not ´multiprocessing´. The latter results in:
´´´python
# This results in TypeError:
#from multiprocessing.pool import Pool
# This works:
from billiard import Pool
´´´
>TypeError: Pickling an AuthenticationString object is disallowed for security reasons


## Docker compose - different environments
Docker and docker-compose are used to build and run this project. To have different development and production environments, one core `docker-compose.yml` file is used together with one of the two override files: `docker-compose.dev.yml` or `docker-compose.prod.yml`.
The main reason for having two environments is that I wanted to make the services update (restar) on code changes.
To manage this, the service containers are built with the `volume` key to share the source folders with the containers, and then the service is started with a `--reload` flag (for the web api) or with `watchgod`.

We don't want this behaviour in production, therefore we omit the `volume`-keys and start without reload. Also, for the web api, we prefer `gunicorn` in place of `uvicorn` (based on FASTapi documentation).

Another difference is that we, in production, doesn't expose all ports. See [Security, section exposing only needed ports](#Exposing only needed ports)section.

## Redis - Warnings and binding
When using the official image `redis:6.2-alpine` out of the box one get some warnings:
>WARNING overcommit_memory is set to 0! Background save may fail under low memory condition.

The files `./redis/init.sh` and `./redis/.sysctl.conf` handles this and sets `vm.overcommit_memory=1`.

>Warning: no config file specified, using the default config.

The file `./redis/redis.conf` is added so that you can add custom configs. The file used is the same as [this one](https://raw.githubusercontent.com/redis/redis/6.2/redis.conf).

## Security

First of all; I'm not a security expert. But some things worth mentioning...

### Non-root users

Non-root users are running the services in the docker files, according to [this post](https://medium.com/@mccode/processes-in-containers-should-not-run-as-root-2feae3f0df3b).
In Docerfile(s), creating user with:

```dockerfile
RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser appuser
```

And set user with:

```dockerfile
USER appuser
```

### Exposing only needed ports

The docker compose differ between ports that are open outside the container (host ports):

```yaml
ports:
   - 8080:8080
```

and ports that are only available to linked services:

```yaml
expose:
   - 5555
```

In the production environment, only the webapi and the flower services are available to the host machine.
In dev everything is exposed to the host, for debugging purposes.

## Considerations

* Consider to change Dockerfile(s) so that pip install is not done by root, but instead create a virtual environment and install as normal user - less chance of messing up any python dependencies already in the image.
* Add ngingx on top of Gunicorn and add some ssl (https).
* Consider Redis Persistence to keep results, even though the service goes down: [](https://redis.io/topics/persistence)
* Consider adding different networks for the different services (nginx in front; api and flower in middle; redis and celery_worker in back)

