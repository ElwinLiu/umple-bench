# Generate Umple state machine

Create `/app/credit_card.ump` using Umple syntax.

## Requirements

- Use valid Umple identifiers (no spaces in state/event identifiers). For example: `preApproval`, `onHold`, `notOnHold`.
- Define a class called `CreditCardApplication` with two separate state machine attributes declared directly in the class body (do not wrap them inside another `state { ... }` block): one named `process` for the approval workflow, and one named `accountStatus` for the hold status.
- The different stages of the approval process must be included: Pre Approval, Cancelled, Complete, Failed.
- The status of the account must be included: On Hold, Not On Hold.
- The process starts in Pre Approval.
- From Pre Approval, the process can be cancelled (Pre Approval → Cancelled).
- From Pre Approval, the process can be put on hold (Pre Approval → On Hold).
- From On Hold, the process can be cancelled (On Hold → Cancelled).
- From On Hold, the process can complete (On Hold → Complete).
- From Pre Approval, the process can complete (Pre Approval → Complete).
- From Pre Approval, the process can fail (Pre Approval → Failed).
- From On Hold, the process can fail (On Hold → Failed).
- In `accountStatus`, the initial state is Not On Hold.
- In `accountStatus`, putting the account on hold transitions Not On Hold → On Hold.
- In `accountStatus`, releasing a hold transitions On Hold → Not On Hold.

Do not create any other classes or files. The only output should be `/app/credit_card.ump`.
