#!/bin/bash
set -e

# Seed database if it doesn't exist
if [ ! -f /app/data/studob.db ]; then
    echo "--- Seeding database ---"
    python /app/scripts/seed_data.py
    echo "--- Seed complete ---"
fi

echo "--- Starting server ---"
exec python /app/main.py
