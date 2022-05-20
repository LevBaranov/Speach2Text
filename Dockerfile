FROM python:3.10-alpine

RUN apk update && apk add  --no-cache ffmpeg flac postgresql-dev gcc python3-dev musl-dev postgresql-client

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD python ./bot.py