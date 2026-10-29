.PHONY: format format-check test e2e e2e-up e2e-down

format:
	black tpbackend e2e

format-check:
	black --check tpbackend e2e

test:
	pytest -v

E2E_COMPOSE = docker compose -f e2e/docker-compose.yml

# spins up a fresh postgres + backend (no discord) in docker, runs e2e tests, tears it down
e2e:
	$(MAKE) e2e-up
	pytest -v e2e; status=$$?; $(MAKE) e2e-down; exit $$status

# leave the environment running to iterate on tests with `pytest e2e`
e2e-up:
	$(E2E_COMPOSE) up -d --build --wait

e2e-down:
	$(E2E_COMPOSE) down -v

dev:
	make format
	make test
	docker build --progress plain -t tpbackend:latest .
	docker compose up -d
	docker compose logs -f

down:
	docker compose down
