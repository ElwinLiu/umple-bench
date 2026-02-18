# Generate Umple state machine

Create `/app/agent.ump` using Umple syntax.

## Requirements

- Define a class called `AgentLoop` with a state machine attribute named `state`.
- The agent loop waits in an idle mode until a run is started or continued, then it enters the assistant turn (idle → assistant turn).
- During the assistant turn, if the assistant requests tool execution, the agent loop enters the tool turn (assistant turn → tool turn).
- During the assistant turn, if the assistant completes its response, the agent loop proceeds to a queue check step (assistant turn → queue check).
- During the assistant turn, if the assistant fails or aborts, the agent loop ends the run.
- During the tool turn, if a requested tool requires permission, the agent loop pauses to await a permission decision (tool turn → awaiting permission).
- During the tool turn, when tool execution completes, the agent loop returns to the assistant turn (tool turn → assistant turn).
- During the tool turn, a steering interrupt can immediately return the loop to the assistant turn (tool turn → assistant turn).
- When awaiting tool permission, granting permission allows the agent loop to resume tool execution (awaiting permission → tool turn).
- When awaiting tool permission, denying permission returns the agent loop to the assistant turn without continuing tool execution (awaiting permission → assistant turn).
- After the assistant completes, if a queued message is available, the agent loop continues with another assistant turn (queue check → assistant turn).
- After the assistant completes, if no queued message is available, the agent loop ends the run.
- After the run ends, the agent loop can be reset back to idle.

Do not create any other classes or files. The only output should be `/app/agent.ump`.
