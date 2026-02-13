FROM python:3.11-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends openjdk-21-jre-headless \
  && rm -rf /var/lib/apt/lists/*

COPY umple.jar /opt/umple/umple.jar

WORKDIR /app
