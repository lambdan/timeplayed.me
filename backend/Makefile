.PHONY: format format-check test

format:
	black conftest.py tpbackend

format-check:
	black --check conftest.py tpbackend

test:
	pytest -v

dev:
	make format
	make test
	docker build --progress plain -t tpbackend:latest .
	docker compose up -d
	docker compose logs -f

down:
	docker compose down
