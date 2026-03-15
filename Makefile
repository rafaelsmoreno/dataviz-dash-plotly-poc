.PHONY: up down build logs shell clean test

## Start the full stack (data-init + dash) in detached mode
up:
	docker compose up --build -d

## Tail logs
logs:
	docker compose logs -f

## Stop and remove containers
down:
	docker compose down

## Rebuild the dash image without cache
build:
	docker compose build --no-cache dash

## Open a shell in the running dash container
shell:
	docker compose exec dash /bin/bash

## Remove containers + the data volume (full reset — re-downloads all data)
clean:
	docker compose down -v

## Run smoke tests inside Docker (no data files required)
test:
	docker compose run --rm --no-deps \
	  -e DATA_DIR=/data \
	  dash pytest /app/tests/ -v
