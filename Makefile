.PHONY: up down build logs shell clean

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
