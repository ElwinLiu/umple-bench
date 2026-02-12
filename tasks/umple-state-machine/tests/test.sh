#!/bin/bash
set -euo pipefail

UMPLE_JAR="/opt/umple/umple.jar"
UMPLE_FILE="/app/door.ump"
REWARD_FILE="/logs/verifier/reward.txt"

mkdir -p /logs/verifier

fail() {
  echo "$1" >&2
  echo 0 > "$REWARD_FILE"
  exit 1
}

if [ ! -f "$UMPLE_FILE" ]; then
  fail "Missing $UMPLE_FILE"
fi

java -jar "$UMPLE_JAR" -g Python "$UMPLE_FILE" || fail "Umple generation failed"

if [ ! -f "/app/Door.py" ]; then
  fail "Door.py was not generated"
fi

python /tests/test_state_machine.py || fail "State machine verification failed"

echo 1 > "$REWARD_FILE"
