FROM --platform=linux/amd64 python:3.9.10-slim-buster

WORKDIR /

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY exporter.py app.py

CMD ["python3", "app.py"]
