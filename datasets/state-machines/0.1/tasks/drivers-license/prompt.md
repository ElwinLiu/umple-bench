You are generating an Umple model file (state machine).

Input files:
- Requirements: $REQ_PATH

Output requirements:
- Write a single Umple model to: $SUBMISSION_PATH
- Do NOT wrap the output in Markdown code fences.

Model requirements (use these names EXACTLY so tests can verify):
- Define a class named: DriversLicense
- Inside it, define: stateMachine { ... }
- States (exact identifiers):
  - Applied
  - KnowledgeTestPassed
  - RoadTestPassed
  - Licensed
  - Suspended
- Transitions (exact event identifiers and targets):
  - Applied: passKnowledge -> KnowledgeTestPassed;
  - KnowledgeTestPassed: passRoad -> RoadTestPassed;
  - RoadTestPassed: issue -> Licensed;
  - Licensed: suspend -> Suspended;
  - Suspended: reinstate -> Licensed;

Keep the model minimal: only what is needed for the state machine above.
