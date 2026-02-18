#!/bin/bash
set -euo pipefail

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  echo "Usage: $0 <task-name> <output-file> [difficulty]"
  echo "Example: $0 umple-state-machine-elevator elevator.ump medium"
  exit 1
fi

TASK_NAME="$1"
OUTPUT_FILE="$2"
DIFFICULTY="${3:-medium}"
TASK_DIR="tasks/$TASK_NAME"
JAR_SOURCE="tasks/umple-state-machine-door/environment/umple.jar"

if [ -e "$TASK_DIR" ]; then
  echo "Task already exists: $TASK_DIR"
  exit 1
fi

mkdir -p "$TASK_DIR"/{environment,solution,tests}

cat > "$TASK_DIR/environment/Dockerfile" <<'EOF'
FROM eclipse-temurin:21-jdk-jammy

COPY umple.jar /opt/umple/umple.jar

WORKDIR /app
EOF

if [ -f "$JAR_SOURCE" ]; then
  cp "$JAR_SOURCE" "$TASK_DIR/environment/umple.jar"
else
  echo "WARNING: $JAR_SOURCE not found. Copy umple.jar manually."
fi

cat > "$TASK_DIR/instruction.md" <<EOF
# Generate Umple state machine

Create "/app/$OUTPUT_FILE" using Umple syntax.

## Requirements

- Replace this section with concrete state and transition requirements.
- Keep requirements deterministic and testable.

Do not create any other classes or files. The only output should be "/app/$OUTPUT_FILE".
EOF

cat > "$TASK_DIR/task.toml" <<EOF
version = "1.0"

[metadata]
author_name = "Elwin"
author_email = "elwin@example.com"
difficulty = "$DIFFICULTY"
category = "state-machine"
tags = ["umple", "state-machine"]
source = "https://umple.org/testmanual/RequirementsExamples.html"

[verifier]
timeout_sec = 300.0

[agent]
timeout_sec = 300.0

[environment]
build_timeout_sec = 600.0
cpus = 1
memory_mb = 2048
storage_mb = 10240
allow_internet = true
EOF

cat > "$TASK_DIR/solution/solve.sh" <<EOF
#!/bin/bash
set -euo pipefail

cat > /app/$OUTPUT_FILE <<'UMP'
class TODO {
  sm {
    Start {}
  }
}
UMP
EOF

cat > "$TASK_DIR/tests/test.sh" <<EOF
#!/bin/bash
set -euo pipefail

UMPLE_JAR="/opt/umple/umple.jar"
UMPLE_FILE="/app/$OUTPUT_FILE"
REWARD_FILE="/logs/verifier/reward.txt"
mkdir -p /logs/verifier

fail() {
  echo "FAIL: $1"
  echo 0 > "$REWARD_FILE"
  exit 0
}

if [ ! -f "$UMPLE_FILE" ]; then
  fail "$UMPLE_FILE not found"
fi

java -jar "$UMPLE_JAR" "$UMPLE_FILE" >/tmp/umple_output.txt 2>&1 || fail "Umple syntax errors found"

echo 1 > "$REWARD_FILE"
echo "PASS"
EOF

chmod +x "$TASK_DIR/solution/solve.sh" "$TASK_DIR/tests/test.sh"

echo "Created task scaffold at $TASK_DIR"
