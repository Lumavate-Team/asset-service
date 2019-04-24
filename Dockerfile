FROM ubuntu:16.04 as common

RUN apt-get update --fix-missing \
    && apt-get install -y wget git

ARG lumavate_exceptions_branch=master
ARG lumavate_signer_branch=master
ARG lumavate_token_branch=master
ARG lumavate_request_branch=master
ARG lumavate_properties_branch=master
ARG lumavate_service_util_branch=master

RUN apt-get update && apt-get install -y git \
  && mkdir /root/.ssh/ \
  && touch /root/.ssh/known_hosts \
  && ssh-keyscan github.com >> /root/.ssh/known_hosts \
  && mkdir /python_packages \
  && cd /python_packages \
  && git clone https://github.com/LabelNexus/python-exceptions.git lumavate_exceptions \
  && cd lumavate_exceptions \
  && git checkout $lumavate_exceptions_branch \
  && rm -rf /python_packages/lumavate_exceptions/.git \
  && cd .. \
  && git clone https://github.com/Lumavate-Team/python-signer.git lumavate_signer \
  && cd lumavate_signer \
  && git checkout $lumavate_signer_branch \
  && rm -rf /python_packages/lumavate_signer/.git \
  && cd .. \
  && git clone https://github.com/LabelNexus/python-token.git lumavate_token \
  && cd lumavate_token \
  && git checkout $lumavate_token_branch \
  && rm -rf /python_packages/lumavate_token/.git \
  && cd .. \
  && git clone https://github.com/LabelNexus/python-api-request.git lumavate_request \
  && cd lumavate_request \
  && git checkout $lumavate_request_branch \
  && rm -rf /python_packages/lumavate_request/.git \
  && cd .. \
  && git clone https://github.com/LabelNexus/python-widget-properties.git lumavate_properties \
  && cd lumavate_properties \
  && git checkout $lumavate_properties_branch \
  && rm -rf /python_packages/lumavate_properties/.git \
  && cd .. \
  && git clone https://github.com/Lumavate-Team/python-service-util.git lumavate_service_util \
  && cd lumavate_service_util \
  && git checkout $lumavate_service_util_branch \
  && rm -rf /python_packages/lumavate_service_util/.git

FROM python:3.7.0-alpine

EXPOSE 5000

COPY --from=common /python_packages ./python_packages/
COPY requirements.txt ./

RUN apk add --no-cache \
    postgresql-libs \
  && apk add --no-cache --virtual .build-deps \
    gcc \
    git \
    libc-dev \
    libgcc \
    linux-headers \
    libffi-dev \
    libressl-dev \
    curl \
    musl-dev \
    postgresql-dev \
  && pip3 install -r requirements.txt \
  && rm -rf .git \
  && mkdir -p /app \
  && apk del .build-deps

ENV PYTHONPATH /python_packages
WORKDIR /app
COPY ./app /app

ENV APP_SETTINGS config/dev.cfg

CMD gunicorn app:app -b 0.0.0.0:5000 --workers 4 --worker-class eventlet --reload
