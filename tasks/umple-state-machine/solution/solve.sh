#!/bin/bash
set -euo pipefail

cat > /app/door.ump <<'UMP'
class Door {
  sm {
    Closed {
      open -> Open;
      lock -> Locked;
    }
    Open {
      close -> Closed;
    }
    Locked {
      unlock -> Closed;
    }
  }
}
UMP

echo "Wrote /app/door.ump"
