SHELL := /bin/bash

.PHONY: run docker-run test lint clean docker-build deploy-cloudrun help

# デフォルトターゲット
all: run

# ローカル環境で起動
run:
	@echo "ローカル環境で起動中..."
	./start_local.sh

# Dockerで起動
docker-run:
	@echo "Dockerで起動中..."
	./start_docker.sh

# テスト実行
test:
	@echo "テスト実行中..."
	pytest -q

# 構文チェック
lint:
	@echo "構文チェック中..."
	find . -name "*.py" -not -path "./.venv/*" -exec python -m py_compile {} +

# クリーンアップ
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache .coverage

# Dockerイメージビルド
docker-build:
	docker build -t sales-saas .

# Cloud Run へデプロイ
deploy-cloudrun:
	gcloud run services replace cloudrun/cloudrun.yaml --region=asia-northeast1 \
		--set-env-vars="FIRESTORE_TENANT_ID=$(FIRESTORE_TENANT_ID),OPENAI_API_SECRET_NAME=$(OPENAI_API_SECRET_NAME),STORAGE_PROVIDER=firestore"

# ヘルプ
help:
	@echo "利用可能なコマンド:"
	@echo "  run         - ローカル環境で起動"
	@echo "  docker-run  - Dockerで起動"
	@echo "  test        - テスト実行"
	@echo "  lint        - 構文チェック"
	@echo "  clean       - クリーンアップ"
	@echo "  docker-build- Dockerイメージビルド"
	@echo "  deploy-cloudrun- Cloud Run にデプロイ"
	@echo "  help        - このヘルプを表示"
