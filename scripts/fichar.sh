#!/bin/bash
# ================================================================
# Run Navidian bot using Docker
# Uses environment variables: NAVIDIAN_USER, NAVIDIAN_PASSWORD, NAVIDIAN_TELEWORK, NAVIDIAN_COMPENSATION, NAVIDIAN_PAUSE
# ================================================================

echo "$(date)::: Starting Navidian bot"

cd "$(dirname "$0")/.."

docker compose run --rm navidian-bot

echo "$(date)::: Navidian bot finished"