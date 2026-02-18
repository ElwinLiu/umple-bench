#!/bin/bash

cat > /app/agent.ump << 'EOF'
class AgentLoop {
  state {
    idle {
      startRun() -> assistantTurn;
      continueRun() -> assistantTurn;
    }
    assistantTurn {
      requestTool() -> toolTurn;
      completeResponse() -> queueCheck;
      failOrAbort() -> end;
    }
    toolTurn {
      requiresPermission() -> awaitingPermission;
      completeTool() -> assistantTurn;
      steeringInterrupt() -> assistantTurn;
    }
    awaitingPermission {
      grantPermission() -> toolTurn;
      denyPermission() -> assistantTurn;
    }
    queueCheck {
      hasQueuedMessage() -> assistantTurn;
      noQueuedMessages() -> end;
    }
    end {
      reset() -> idle;
    }
  }
}
EOF
