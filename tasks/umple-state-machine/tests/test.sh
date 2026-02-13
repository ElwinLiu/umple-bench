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

# Just verify Umple can parse the file (no code generation needed)
java -jar "$UMPLE_JAR" "$UMPLE_FILE" || fail "Umple parsing failed"

# Verify the file contains expected state machine content
if ! grep -q "sm {" "$UMPLE_FILE"; then
  fail "State machine not defined"
fi

if ! grep -q "Closed" "$UMPLE_FILE"; then
  fail "Closed state not defined"
fi

if ! grep -q "Open" "$UMPLE_FILE"; then
  fail "Open state not defined"
fi

if ! grep -q "Locked" "$UMPLE_FILE"; then
  fail "Locked state not defined"
fi

echo 1 > "$REWARD_FILE"
