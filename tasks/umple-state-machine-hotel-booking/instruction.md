# Generate Umple state machine

Create `/app/room.ump` using Umple syntax.

## Requirements

- Define a class called `Room` with a state machine attribute named `status`.
- On any given day (overnight from one night to the following morning), each room can be either available, allocated to a guest, or unavailable due to maintenance.
- The room starts in the available state.
- When a room is available, it can be allocated to a guest (available → allocated) or marked for maintenance (available → unavailable).
- When a room is allocated to a guest, it can be released (allocated → available).
- When a room is unavailable due to maintenance, it can be completed and made available (unavailable → available).

Do not create any other classes or files. The only output should be `/app/room.ump`.
