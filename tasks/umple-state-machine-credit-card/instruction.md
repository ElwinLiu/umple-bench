# Generate Umple state machine

Create `/app/credit_card.ump` using Umple syntax.

## Requirements

- Define a class called `CreditCardApplication` with two state machine attributes: one named `process` for the approval workflow, and one named `accountStatus` for the hold status.
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
- The transaction can be successful or fail.

Do not create any other classes or files. The only output should be `/app/credit_card.ump`.
