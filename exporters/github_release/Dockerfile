FROM alpine/flake8:latest as linter
WORKDIR /apps/
COPY . /apps/
## ingore E501 line too long (XX > 79 characters)
RUN flake8 --ignore="E501" *.py

FROM --platform=linux/amd64 python:3.11-slim-buster

WORKDIR /

RUN apt-get update && apt-get install -y gcc g++
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir
RUN groupadd -r exporter && useradd -r -g exporter exporter

COPY --from=linter /apps/exporter.py app.py
COPY --from=linter /apps/projects.yml projects.yml

USER exporter
CMD ["python3", "app.py"]
