THIS_FILE := $(lastword $(MAKEFILE_LIST))
.PHONY: build buildup up start down destroy stop restart logs logs-api ps login-api login-celery_worker login-redis

prod=docker-compose.prod.yml
dev=docker-compose.dev.yml

ifeq ($(e), prod)
	envcompose=$(prod)
else
	envcompose=$(dev)
endif

ifeq ($(d), false)
	sdetmak=
else
	sdet=-d
endif

# COLORS
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

TARGET_MAX_CHAR_NUM=20
## Show help
help:
	@echo 'usage: make target [arg=arg, *]'
	@echo
	@echo 'targets:'
	@echo '          help: this text'
	@echo '          build: build image(s), argument c and e available'
	@echo '          buildup: build image(s), create and start container(s), argument c, d, e available'
	@echo '          up: start container(s), argument c, d, e available'
	@echo '          start: start container(s), argument c and e available'
	@echo '          down: stop and remove container(s), argument c, e available'
	@echo '          stop: stop container(s), argument c, e available'
	@echo '          restart: same as make stop & make start in sequenze, argument c, d and e available'
	@echo '          logs: return logs of container(s), argument c and e available'
	@echo '          logs-api: return logs for api container, argument e available'
	@echo '          ps: list containers'
	@echo '          login-api: start interactive prompt for container api, argument e available'
	@echo '          login-celery_worker: start interactive prompt for container celery_worker, argument e available'
	@echo '          login-redis: start interactive prompt for container redis, argument e available'
	@echo '          Tip: leave login with command "exit" or ctrl-D'
	@echo
	@echo 'arguments:'
	@echo '          c: container name(s), usage: c=container_name or c="container1 container2 ..."'
	@echo '          d: run command detached or not, default is detatched, usage: d=false'
	@echo '             Detached mode: Run containers in the background'
	@echo '          e: which docker-compose environment file to use, default is docker-compose.dev.yml'
	@echo '             usage: e=prod to use docker-compose.prod.yml"'
	@echo
	@echo 'EXAMPLE:'
	@echo '          make buildup c="redis flower" d=false e=prod'
	@echo '          will build, create and start the container (in "undetatched mode") for redis and flower,'
	@echo '          using the docker-compose.yml with overrides from docker-compose.prod.yml'

build:
	docker-compose -f docker-compose.yml -f $(envcompose) build $(c)
buildup:
	docker-compose -f docker-compose.yml -f $(envcompose) up --build $(sdet) --no-deps $(c)
up:
	docker-compose -f docker-compose.yml -f $(envcompose) up $(sdet) $(c)
start:
	docker-compose -f docker-compose.yml -f $(envcompose) start $(c)
down:
	docker-compose -f docker-compose.yml -f $(envcompose) down $(c)
destroy:
	docker-compose -f docker-compose.yml -f $(envcompose) down -v $(c)
stop:
	docker-compose -f docker-compose.yml -f $(envcompose) stop $(c)
restart:
	docker-compose -f docker-compose.yml -f $(envcompose) stop $(c)
	docker-compose -f docker-compose.yml -f $(envcompose) up $(sdet) $(c)
logs:
	docker-compose -f docker-compose.yml -f $(envcompose) logs --tail=100 -f $(c)
logs-api:
	docker-compose -f docker-compose.yml -f $(envcompose) logs --tail=100 -f api
ps:
	docker-compose -f docker-compose.yml -f $(envcompose) ps
login-api:
	docker-compose -f docker-compose.yml -f $(envcompose) exec api /bin/bash
login-celery_worker:
	docker-compose -f docker-compose.yml -f $(envcompose) exec celery_worker /bin/bash
login-redis:
	docker-compose -f docker-compose.yml -f $(envcompose) exec redis /bin/bash
