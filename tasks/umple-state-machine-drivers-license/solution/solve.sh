#!/bin/bash

cat > /app/license.ump << 'EOF'
class License {
  level {
    noLicense {
      passG1Test() -> G1;
    }
    G1 {
      passG2Test() -> G2;
      expire() -> noLicense;
      suspend() -> suspendedG1;
    }
    G2 {
      passGTest() -> G;
      expire() -> noLicense;
      suspend() -> suspendedG2;
    }
    G {
      renew() -> G;
      suspend() -> suspendedG;
    }
    suspendedG1 {
      reinstate() -> G1;
    }
    suspendedG2 {
      reinstate() -> G2;
    }
    suspendedG {
      reinstate() -> G;
    }
  }
}
EOF
