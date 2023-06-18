FROM python:3.11-rc-slim-bullseye

WORKDIR /api

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . . 
