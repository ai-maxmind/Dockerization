FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg2 \
    lsb-release \
    bzip2 \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libgdk-pixbuf2.0-0 \
    libx11-xcb1 \
    libxcb-render0 \
    libxcb-shm0 \
    libxrender1 \
    libfontconfig1 \
    libxext6 \
    libxcomposite1 \
    libgl1-mesa-glx \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*


RUN wget https://ftp.mozilla.org/pub/firefox/releases/120.0/linux-x86_64/en-US/firefox-120.0.tar.bz2 -O /tmp/firefox.tar.bz2 \
    && tar -xjf /tmp/firefox.tar.bz2 -C /opt/ \
    && ln -sf /opt/firefox/firefox /usr/bin/firefox \
    && rm /tmp/firefox.tar.bz2

RUN wget -q "https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz" \
    && tar -xvzf geckodriver-v0.33.0-linux64.tar.gz -C /usr/local/bin \
    && rm geckodriver-v0.33.0-linux64.tar.gz

COPY requirements.txt /usr/src/app/requirements.txt
RUN pip install -r /usr/src/app/requirements.txt

COPY .env           /usr/src/app/.env
COPY common.py      /usr/src/app/common.py
COPY AutoCrawler.py /usr/src/app/AutoCrawler.py
COPY ImportData.py  /usr/src/app/ImportData.py

WORKDIR /usr/src/app

ENTRYPOINT ["sh", "-c", "python AutoCrawler.py && python ImportData.py"]
