#!/bin/bash
# Script to run Navidian bot with random delay and holiday check
# Uses environment variables

echo "$(date)::: Delayed execution starting"

# Example holidays (generic)
EXCLUDED_DAYS=(
  "2026-01-01"
  "2026-12-25"
)

TODAY=$(date +%Y-%m-%d)
for EXCLUDED in "${EXCLUDED_DAYS[@]}"; do
    if [[ "$TODAY" == "$EXCLUDED" ]]; then
        echo "$(date)::: Today is an excluded holiday ($TODAY)"
        exit 0
    fi
done

# Random delay 0-15 min
WAIT_SECONDS=$((RANDOM % 900))
echo "$(date)::: Sleeping for $WAIT_SECONDS seconds before running"
sleep $WAIT_SECONDS

# Run bot
cd $(dirname "$0")/..
docker compose run --rm navidian-bot

echo "$(date)::: Finished delayed execution"