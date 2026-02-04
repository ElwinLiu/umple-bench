You are generating an Umple model file (state machine).

Input files:
- Requirements: $REQ_PATH

Output requirements:
- Write a single Umple model to: $SUBMISSION_PATH
- Do NOT wrap the output in Markdown code fences.

Model requirements (use these names EXACTLY so tests can verify):
- Define a class named: HotelBooking
- Inside it, define: stateMachine { ... }
- States (exact identifiers):
  - Browsing
  - Reserved
  - CheckedIn
  - CheckedOut
  - Cancelled
- Transitions (exact event identifiers and targets):
  - Browsing: reserve -> Reserved;
  - Reserved: cancel -> Cancelled;
  - Reserved: checkIn -> CheckedIn;
  - CheckedIn: checkOut -> CheckedOut;

Keep the model minimal: only what is needed for the state machine above.
