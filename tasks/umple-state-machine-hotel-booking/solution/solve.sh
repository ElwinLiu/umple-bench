#!/bin/bash

cat > /app/room.ump << 'EOF'
class Room {
  status {
    available {
      allocate() -> allocated;
      startMaintenance() -> unavailable;
    }
    allocated {
      release() -> available;
    }
    unavailable {
      completeMaintenance() -> available;
    }
  }
}
EOF
