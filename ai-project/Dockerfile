FROM tensorflow/tensorflow:latest
WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && \
    pip install -r requirements.txt
EXPOSE 8888
