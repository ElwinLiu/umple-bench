FROM --platform=linux/amd64 eclipse-temurin:21-jdk-jammy

RUN apt-get update && apt-get install -y --no-install-recommends python3 curl ca-certificates xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    NODE_VERSION="v22.22.0"; \
    ARCHIVE="node-${NODE_VERSION}-linux-x64.tar.xz"; \
    curl -fsSLO "https://nodejs.org/dist/${NODE_VERSION}/${ARCHIVE}"; \
    tar -xJf "${ARCHIVE}" -C /usr/local --strip-components=1; \
    rm -f "${ARCHIVE}"; \
    npm install -g @mariozechner/pi-coding-agent@latest; \
    pi --version

RUN set -eux; \
    mkdir -p /tmp/txl-install; \
    cd /tmp/txl-install; \
    curl -fsSL -X POST -d "Platform=linux64&Submit=I+Agree" https://www.txl.ca/cgi-bin/txl-download.cgi -o txl-download.html; \
    TXL_REL_PATH="$(grep -o '\.\./download/[^\"[:space:]]*linux64.tar.gz' txl-download.html | head -n1 | sed 's#^\.\./##')"; \
    test -n "$TXL_REL_PATH"; \
    curl -fsSL "https://www.txl.ca/${TXL_REL_PATH}" -o txl.tar.gz; \
    tar -xzf txl.tar.gz --strip-components=1; \
    ./InstallTxl; \
    rm -rf /tmp/txl-install

COPY umple.jar /opt/umple/umple.jar

WORKDIR /app
