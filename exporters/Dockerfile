FROM --platform=linux/amd64 python:3.8-slim-buster

ARG exporter

WORKDIR /

RUN apt update && apt install -y gcc g++
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ${exporter}.py app.py
COPY functions.py functions.py

CMD ["python3", "app.py"]
