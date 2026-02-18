#!/bin/bash
set -euo pipefail

UMPLE_JAR="/opt/umple/umple.jar"
UMPLE_FILE="/app/credit_card.ump"
REWARD_FILE="/logs/verifier/reward.txt"

mkdir -p /logs/verifier

fail() {
  echo "FAIL: $1" >&2
  echo 0 > "$REWARD_FILE"
  exit 1
}

# --- Step 1: File existence ---
if [ ! -f "$UMPLE_FILE" ]; then
  fail "Missing $UMPLE_FILE"
fi

# --- Step 2: Umple syntax validation ---
if ! java -jar "$UMPLE_JAR" "$UMPLE_FILE" 2>&1 | tee /tmp/umple_parse.txt; then
  fail "Umple parse command failed"
fi
if grep -qi "error" /tmp/umple_parse.txt; then
  fail "Umple parsing errors detected"
fi

# --- Step 3: Structural sanity check ---
if ! grep -q -- "->" "$UMPLE_FILE"; then
  fail "No transitions found in $UMPLE_FILE"
fi

# --- Step 4: Generate Python code from Umple ---
cd /app
if ! java -jar "$UMPLE_JAR" -g Python "$UMPLE_FILE" 2>&1 | tee /tmp/umple_gen.txt; then
  fail "Python code generation command failed"
fi
if grep -qi "error" /tmp/umple_gen.txt; then
  fail "Python code generation failed"
fi

if [ ! -f /app/CreditCardApplication.py ]; then
  fail "CreditCardApplication.py was not generated — is the class named 'CreditCardApplication'?"
fi

# --- Step 5: Behavioral state-machine verification (Python runtime) ---
if ! python3 /tests/test_state_machine.py 2>&1 | tee /tmp/python_test.txt; then
  fail "State machine transition tests failed"
fi

echo "PASS: All structural and behavioral checks passed"
echo 1 > "$REWARD_FILE"
