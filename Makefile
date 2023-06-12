SHELL=/usr/bin/bash

all: update start

app:
	@nohup python -m app -O [StudCabSync] &

debug:
	@python -m app [StudCabSync] [DEBUG]

start: app

update: install

install:
	@pip install -r requirements.txt

.PHONY: all app start update install
