#!/bin/sh
set -eu
docker compose pull || true
docker compose build --pull
docker compose up -d --remove-orphans
docker compose ps
