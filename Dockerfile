FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libtiff-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

RUN pip install --no-cache-dir RPi.GPIO Adafruit_SSD1306 pyserial Pillow requests six flask

RUN mkdir -p /home/MAPS6_NBIOT /mnt/SD

COPY . /home/MAPS6_NBIOT/
COPY ARIALUNI.TTF /home/

WORKDIR /home/MAPS6_NBIOT

EXPOSE 5000

CMD ["python", "main.py"]
