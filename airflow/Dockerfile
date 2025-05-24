FROM apache/airflow:2.6.3-python3.8

ARG http_proxy
ARG https_proxy

ENV http_proxy=${http_proxy}
ENV https_proxy=${https_proxy}
ENV HTTP_PROXY=${http_proxy}
ENV HTTPS_PROXY=${https_proxy}

USER root

RUN echo "Acquire::http::Proxy \"${http_proxy}\";" > /etc/apt/apt.conf.d/01proxy && \
    echo "Acquire::https::Proxy \"${https_proxy}\";" >> /etc/apt/apt.conf.d/01proxy && \
    apt-get update && \
    apt-get install -y --no-install-recommends sudo apt-utils tzdata && \
    echo "airflow ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt .
RUN pip install --proxy ${http_proxy} -r requirements.txt
