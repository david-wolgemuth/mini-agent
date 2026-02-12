PROJECT_DIR := $(shell pwd)
AGENT_HOME := /home/agent/mini-agent

.PHONY: setup run run-sandbox setup-sandbox sync-sandbox help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

setup: ## First-time project setup (uv + deps)
	uv sync

run: ## Run mini-agent locally (no sandbox)
	uv run mini-agent

run-confirm: ## Run with confirmation before each exec
	uv run mini-agent --confirm

setup-sandbox: ## Create restricted agent user and install project
	sudo useradd -m -s /bin/bash agent 2>/dev/null || true
	sudo -u agent -i bash -c "which uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh"
	sudo mkdir -p $(AGENT_HOME)
	sudo rsync -a --delete \
		--exclude='.venv' \
		--exclude='__pycache__' \
		--exclude='.git' \
		$(PROJECT_DIR)/ $(AGENT_HOME)/
	sudo chown -R agent:agent $(AGENT_HOME)
	sudo -u agent -i bash -c "cd $(AGENT_HOME) && uv sync"

sync-sandbox: ## Sync latest code to sandbox user
	sudo rsync -a --delete \
		--exclude='.venv' \
		--exclude='__pycache__' \
		--exclude='.git' \
		$(PROJECT_DIR)/ $(AGENT_HOME)/
	sudo chown -R agent:agent $(AGENT_HOME)
	sudo -u agent -i bash -c "cd $(AGENT_HOME) && uv sync"

run-sandbox: ## Run as sandboxed agent user
	sudo -u agent -i bash -c "cd $(AGENT_HOME) && uv run mini-agent"
