FROM python:3.10-alpine

RUN apk update && apk add  --no-cache ffmpeg flac

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD python ./bot.py