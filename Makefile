# ===========================================
# SarfX Enhanced - Makefile
# ===========================================
# Commandes simplifiées pour Docker Compose

.PHONY: help dev prod build up down logs shell clean seed test

# Variables
COMPOSE_BASE = docker-compose -f docker-compose.yml
COMPOSE_DEV = $(COMPOSE_BASE) -f docker-compose.dev.yml
COMPOSE_PROD = $(COMPOSE_BASE) -f docker-compose.prod.yml

# Couleurs
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m # No Color

# ===========================================
# AIDE
# ===========================================
help: ## Affiche cette aide
	@echo ""
	@echo "$(GREEN)🚀 SarfX Docker Commands$(NC)"
	@echo "========================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ===========================================
# DÉVELOPPEMENT
# ===========================================
dev: ## Démarre l'environnement de développement
	@echo "$(GREEN)🔧 Starting development environment...$(NC)"
	$(COMPOSE_DEV) up --build

dev-d: ## Démarre le dev en arrière-plan
	@echo "$(GREEN)🔧 Starting development environment (detached)...$(NC)"
	$(COMPOSE_DEV) up --build -d

dev-down: ## Arrête l'environnement de développement
	@echo "$(RED)⏹️  Stopping development environment...$(NC)"
	$(COMPOSE_DEV) down

# ===========================================
# PRODUCTION
# ===========================================
prod: ## Démarre l'environnement de production
	@echo "$(GREEN)🚀 Starting production environment...$(NC)"
	$(COMPOSE_PROD) up --build -d

prod-down: ## Arrête l'environnement de production
	@echo "$(RED)⏹️  Stopping production environment...$(NC)"
	$(COMPOSE_PROD) down

# ===========================================
# COMMANDES GÉNÉRALES
# ===========================================
build: ## Build toutes les images Docker
	@echo "$(GREEN)🔨 Building Docker images...$(NC)"
	$(COMPOSE_BASE) build

up: ## Démarre les services (base uniquement)
	@echo "$(GREEN)▶️  Starting services...$(NC)"
	$(COMPOSE_BASE) up -d

down: ## Arrête tous les services
	@echo "$(RED)⏹️  Stopping all services...$(NC)"
	$(COMPOSE_BASE) down

restart: ## Redémarre tous les services
	@echo "$(YELLOW)🔄 Restarting services...$(NC)"
	$(COMPOSE_BASE) restart

# ===========================================
# LOGS & MONITORING
# ===========================================
logs: ## Affiche les logs de tous les services
	$(COMPOSE_BASE) logs -f

logs-flask: ## Logs de l'application Flask
	$(COMPOSE_BASE) logs -f flask-app

logs-ai: ## Logs du backend IA
	$(COMPOSE_BASE) logs -f ai-backend

logs-mongo: ## Logs de MongoDB
	$(COMPOSE_BASE) logs -f mongo

logs-redis: ## Logs de Redis
	$(COMPOSE_BASE) logs -f redis

ps: ## Liste les conteneurs en cours
	$(COMPOSE_BASE) ps

stats: ## Statistiques des conteneurs
	docker stats --no-stream

# ===========================================
# SHELL & DEBUG
# ===========================================
shell-flask: ## Shell dans le conteneur Flask
	@echo "$(GREEN)🐚 Entering Flask container...$(NC)"
	docker exec -it sarfx-flask /bin/bash

shell-ai: ## Shell dans le conteneur AI
	@echo "$(GREEN)🐚 Entering AI Backend container...$(NC)"
	docker exec -it sarfx-ai /bin/bash

shell-mongo: ## Shell MongoDB
	@echo "$(GREEN)🐚 Entering MongoDB shell...$(NC)"
	docker exec -it sarfx-mongo mongosh SarfX_Enhanced

shell-redis: ## Shell Redis
	@echo "$(GREEN)🐚 Entering Redis CLI...$(NC)"
	docker exec -it sarfx-redis redis-cli

# ===========================================
# DATABASE
# ===========================================
seed: ## Initialise la base de données avec les données de test
	@echo "$(GREEN)🌱 Seeding database...$(NC)"
	docker exec -it sarfx-mongo mongosh SarfX_Enhanced /docker-entrypoint-initdb.d/mongo-init.js

backup: ## Sauvegarde la base de données
	@echo "$(GREEN)💾 Backing up database...$(NC)"
	@mkdir -p backups
	docker exec sarfx-mongo mongodump --db SarfX_Enhanced --archive=/data/db/backup.archive
	docker cp sarfx-mongo:/data/db/backup.archive ./backups/backup-$$(date +%Y%m%d-%H%M%S).archive
	@echo "$(GREEN)✅ Backup saved to backups/$(NC)"

restore: ## Restaure la dernière sauvegarde
	@echo "$(YELLOW)📥 Restoring database...$(NC)"
	@LATEST=$$(ls -t backups/*.archive 2>/dev/null | head -1); \
	if [ -z "$$LATEST" ]; then \
		echo "$(RED)❌ No backup found$(NC)"; \
	else \
		docker cp $$LATEST sarfx-mongo:/data/db/restore.archive; \
		docker exec sarfx-mongo mongorestore --archive=/data/db/restore.archive --drop; \
		echo "$(GREEN)✅ Restored from $$LATEST$(NC)"; \
	fi

# ===========================================
# NETTOYAGE
# ===========================================
clean: ## Supprime les conteneurs et volumes
	@echo "$(RED)🧹 Cleaning up...$(NC)"
	$(COMPOSE_BASE) down -v --remove-orphans

clean-images: ## Supprime aussi les images
	@echo "$(RED)🧹 Cleaning up images...$(NC)"
	$(COMPOSE_BASE) down -v --rmi all --remove-orphans

prune: ## Nettoie Docker (attention: supprime tout!)
	@echo "$(RED)⚠️  Pruning Docker system...$(NC)"
	docker system prune -af --volumes

# ===========================================
# TESTS
# ===========================================
test: ## Lance les tests
	@echo "$(GREEN)🧪 Running tests...$(NC)"
	docker exec sarfx-flask pytest tests/ -v

test-cov: ## Tests avec couverture
	docker exec sarfx-flask pytest tests/ -v --cov=app --cov-report=html

# ===========================================
# HEALTH CHECKS
# ===========================================
health: ## Vérifie l'état des services
	@echo "$(GREEN)🏥 Health check...$(NC)"
	@echo ""
	@echo "Flask App:"
	@curl -sf http://localhost:5050/health && echo " ✅ OK" || echo " ❌ DOWN"
	@echo ""
	@echo "AI Backend:"
	@curl -sf http://localhost:8087/ && echo " ✅ OK" || echo " ❌ DOWN"
	@echo ""
	@echo "MongoDB:"
	@docker exec sarfx-mongo mongosh --eval "db.adminCommand('ping')" --quiet && echo " ✅ OK" || echo " ❌ DOWN"
	@echo ""
	@echo "Redis:"
	@docker exec sarfx-redis redis-cli ping | grep -q PONG && echo " ✅ OK" || echo " ❌ DOWN"

# ===========================================
# QUICK START
# ===========================================
init: ## Initialisation complète (premier lancement)
	@echo "$(GREEN)🚀 Initializing SarfX...$(NC)"
	@echo ""
	@echo "1️⃣  Creating .env file..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "   ✅ Created .env"; else echo "   ⏭️  .env exists"; fi
	@echo ""
	@echo "2️⃣  Building images..."
	$(COMPOSE_DEV) build
	@echo ""
	@echo "3️⃣  Starting services..."
	$(COMPOSE_DEV) up -d
	@echo ""
	@echo "4️⃣  Waiting for MongoDB..."
	@sleep 10
	@echo ""
	@echo "$(GREEN)✅ SarfX is ready!$(NC)"
	@echo ""
	@echo "📱 Flask App:      http://localhost:5050"
	@echo "🤖 AI Backend:     http://localhost:8087"
	@echo "📊 Mongo Express:  http://localhost:8081 (admin/admin123)"
	@echo "📈 Redis Commander: http://localhost:8082"
	@echo ""
