FROM docker.io/python:3.11.3-slim

WORKDIR /build
COPY . .

RUN pip install -e .

WORKDIR /app

RUN rm -rf /build
COPY ./docker/config.yml .

USER 1000

ENTRYPOINT ["scalr-ngine"]
