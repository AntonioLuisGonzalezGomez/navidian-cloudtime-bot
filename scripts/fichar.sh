#!/bin/bash
# Script to run Navidian bot in Docker
# Uses environment variables for credentials

echo "$(date)::: Starting Navidian bot"

cd $(dirname "$0")/..

docker compose run --rm navidian-bot

echo "$(date)::: Navidian bot finished"