FROM python:3.10-alpine

RUN apk add -q --progress --update --no-cache ffmpeg

COPY ./requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r ./requirements.txt && \
    pip install --no-cache /wheels/*

COPY . /app
WORKDIR /app
CMD python ./bot.py