#!/bin/bash

# Kill any existing backfill processes
pkill -f backfill_range.py

# Set up environment
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
export DB_HOST=localhost
export DB_NAME=parking_local
export DB_USER=$USER
export DB_PASSWORD=""
export DB_PORT=5432
export RANGE_START=10516228
export RANGE_END=10516578

# Activate virtual environment
source .venv/bin/activate

# Run with nohup to survive terminal closure
nohup python backfill_range.py > backfill.log 2>&1 &

echo "Backfill started in background. PID: $!"
echo "Log file: backfill.log"
echo "To check progress: tail -f backfill.log"
echo "To check DB: psql -d parking_local -c 'select count(*) from citations;'"
echo "To stop: pkill -f backfill_range.py"
