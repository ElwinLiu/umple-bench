#!/bin/bash
set -e

echo "=== Umple Benchmark Setup ==="
echo ""

# List all tasks
echo "Available tasks in this dataset:"
for task in tasks/*/; do
    task_name=$(basename "$task")
    if [ -f "$task/task.toml" ]; then
        difficulty=$(grep "difficulty" "$task/task.toml" | cut -d'"' -f2)
        echo "  • $task_name ($difficulty)"
    fi
done
echo ""

# Instructions for running
cat << 'EOF'
=== How to Run ===

1. Test a single task with oracle:
   harbor run -p tasks/umple-state-machine-door -a oracle

2. Run all tasks with oracle:
   harbor run -p tasks/ -a oracle

3. Run with an AI agent (concurrent):
   harbor run -p tasks/ -a claude-code -m anthropic/claude-opus-4-1 -n 4 -k 3

4. Run with job config file:
   harbor run -c job.yaml

=== Task Summary ===

• umple-state-machine-door: Door state machine (Closed, Open, Locked)
• umple-state-machine-hotel-booking: Hotel room states (available, allocated, unavailable)
• umple-state-machine-drivers-license: License progression (noLicense→G1→G2→G)
• umple-state-machine-agent-loop: AI agent loop (idle, assistantTurn, toolTurn, awaitingPermission, queueCheck)
• umple-state-machine-credit-card: Credit card approval (preApproval, onHold, complete, failed, cancelled)

All tasks are self-contained with their own Dockerfiles.

See also:
• tasks/README.md for task/output/verifier overview
• scripts/scaffold_umple_task.sh to create new tasks consistently
EOF
