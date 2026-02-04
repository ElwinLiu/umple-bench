# Hotel booking — requirements

Design a state machine for a hotel booking flow:

- A user starts by browsing rooms.
- The user can reserve a room.
- Once reserved, the user can either cancel *before check-in* or check in.
- Once checked in, the user can check out.

Constraints:
- You must not allow check-in unless the booking is reserved.
- You must not allow check-out unless the booking is checked in.
- Cancellation must only be possible from the reserved state (not after check-in).
