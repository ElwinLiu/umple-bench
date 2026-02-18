#!/bin/bash

cat > /app/credit_card.ump << 'EOF'
class CreditCardApplication {
  process {
    preApproval {
      cancel() -> cancelled;
      putOnHold() -> onHold;
      complete() -> complete;
      fail() -> failed;
    }
    onHold {
      cancel() -> cancelled;
      complete() -> complete;
      fail() -> failed;
    }
    cancelled {}
    complete {}
    failed {}
  }
  accountStatus {
    notOnHold {
      hold() -> onHoldStatus;
    }
    onHoldStatus {
      release() -> notOnHold;
    }
  }
}
EOF
