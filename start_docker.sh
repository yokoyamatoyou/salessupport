#!/usr/bin/env bash
set -e

export PORT=${PORT:-8080}
cp -n env.example .env || true
docker compose up --build

