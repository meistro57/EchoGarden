# Makefile

.PHONY: dev-init dev-up dev-stop dev-down test test-unit test-cov test-integration

dev-init:
	cp infra/.env.example infra/.env
	chmod +x scripts/*.sh

dev-up: dev-init
	docker compose -f infra/docker-compose.yml up -d
	sleep 15  # Wait for services
	./scripts/dev_start.sh

dev-stop:
	docker compose -f infra/docker-compose.yml stop

dev-down:
	docker compose -f infra/docker-compose.yml down --volumes --remove-orphans

test:
	python -m pytest tests/ -v

test-unit:
	python -m pytest tests/ -v -m "not integration and not slow"

test-cov:
	python -m pytest tests/ --cov=api --cov=worker --cov-report=term-missing --cov-report=html

test-integration:
	python -m pytest scripts/test_system.py -v