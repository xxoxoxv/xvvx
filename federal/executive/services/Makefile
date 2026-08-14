# AMOS-Federation Makefile
# الهدف: أوامر التطوير الشائعة
# النطاق: federal/executive/services
# المالك: federal/executive/services
# تاريخ الإنشاء: 2026-08-15

.PHONY: help up down restart ps logs migrate seed test lint format ci clean

PYTHON := python3
DOCKER_COMPOSE := docker compose
COMPOSE_FILE := docker-compose.yml

help:
	@echo "AMOS-Federation — أوامر التطوير"
	@echo "  make up          — رفع كل الخدمات"
	@echo "  make down        — إيقاف كل الخدمات"
	@echo "  make restart     — إعادة تشغيل الخدمات"
	@echo "  make ps          — حالة الخدمات"
	@echo "  make logs        — سجلات كل الخدمات"
	@echo "  make migrate     — تشغيل SQL migrations"
	@echo "  make seed        — بيانات أولية"
	@echo "  make test        — تشغيل الاختبارات"
	@echo "  make lint        — فحص الكود (ruff)"
	@echo "  make format      — تنسيق الكود (ruff format)"
	@echo "  make ci          — تشغيل CI محليًا (lint + test + identity check)"
	@echo "  make clean       — تنظيف الملفات المؤقتة"

up:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "Services are up. Check: make ps"

down:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down

restart:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d

ps:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) ps

logs:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f --tail=100

migrate:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) exec -T postgres psql -U amos -d amos_federation -f /docker-entrypoint-initdb.d/001_init.sql
	@echo "Migrations applied."

seed:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) exec -T postgres psql -U amos -d amos_federation -f /docker-entrypoint-initdb.d/002_seed.sql
	@echo "Seed data inserted."

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

lint:
	$(PYTHON) -m ruff check src/ tests/
	@echo "Lint passed."

format:
	$(PYTHON) -m ruff format src/ tests/
	$(PYTHON) -m ruff check --fix src/ tests/

ci: lint test
	$(PYTHON) ../../tools/governance/check_repository_identity.py ../
	@echo "CI checks passed."

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
