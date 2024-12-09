FROM docker.io/python:3.13.1-slim

ENV MPLCONFIGDIR /tmp
RUN pip install --upgrade wheel pip

WORKDIR /build

COPY dist/scalr_ngine-*.whl .
RUN pip install scalr_ngine-*.whl

WORKDIR /app

RUN rm -rf /build
COPY ./docker/config.yml .

USER 1000

ENTRYPOINT ["scalr-ngine"]
