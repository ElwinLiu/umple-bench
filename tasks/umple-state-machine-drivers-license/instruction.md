# Generate Umple state machine

Create `/app/license.ump` using Umple syntax.

## Requirements

- Define a class called `License` with a state machine attribute named `level`.
- The user can have no license, a G1 license, a G2 license or a G license.
- The user starts with no license.
- To get a G1, a test must be completed (no license → G1).
- To get a G2, the user must have a G1 and a test must be completed (G1 → G2).
- To get a G, the user must have a G2 and a test must be completed (G2 → G).
- Each type of license can expire. If a G1 or G2 expires then the license is lost (G1 → no license, G2 → no license).
- If a G expires it can be renewed (G → G).
- Each type of license can be suspended. Use separate suspended states for each license level (G1 → suspendedG1, G2 → suspendedG2, G → suspendedG) so that reinstatement returns to the correct level.
- A suspended license can be reinstated to the level held before suspension (suspendedG1 → G1, suspendedG2 → G2, suspendedG → G).

Do not create any other classes or files. The only output should be `/app/license.ump`.
