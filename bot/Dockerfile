FROM --platform=linux/amd64 ubuntu:22.04

RUN apt update && apt install -y gcc g++ libpq-dev git python3 python3-pip
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app app
COPY alerts_tmpl.yml app/

WORKDIR app

CMD ["python3", "./"]
