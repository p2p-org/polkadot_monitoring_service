FROM --platform=linux/amd64 ubuntu:22.04

WORKDIR /

COPY requirements.txt requirements.txt
COPY update_cache.py update_cache.py
COPY validators.txt validators.txt

RUN apt update && apt install -y gcc g++ libpq-dev git python3 python3-pip
RUN pip3 install -r requirements.txt

CMD ["python3", "update_cache.py"]
