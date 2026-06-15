#!/bin/bash
while true; do
  bash ascii_art.sh
  echo "Starting wordle bot..."
  cd /home/joud/wordle && python3 src_py/bot.py
  echo "Bot crashed with exit code $?. Restarting in 3 seconds..."
  sleep 3
done
