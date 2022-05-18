FROM python:3.10-alpine

RUN apk update && apk add  --no-cache ffmpeg

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir /app
ADD . /app
WORKDIR /app

CMD python ./bot.py