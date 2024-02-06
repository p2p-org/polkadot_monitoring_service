FROM --platform=linux/amd64 python:3.11-slim-buster 

ARG exporter

WORKDIR /

RUN apt-get update && apt-get install -y gcc g++
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir
RUN groupadd -r exporter && useradd -r -g exporter exporter

COPY exporter.py app.py
COPY functions.py functions.py

USER exporter
CMD ["python3", "app.py"]
