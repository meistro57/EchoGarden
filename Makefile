# Makefile

.PHONY: dev-init dev-up dev-stop dev-down test

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
	python scripts/test_system.py