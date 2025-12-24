.PHONY: up down build test

up:
	docker-compose up --build -d

down:
	docker-compose down -v

build:
	docker-compose build

test:
	pytest -q
