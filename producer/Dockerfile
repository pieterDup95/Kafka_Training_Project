FROM python:3.11-slim
WORKDIR /app
COPY zscaler.crt /usr/local/share/ca-certificates/zscaler.crt
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --cert /etc/ssl/certs/ca-certificates.crt confluent-kafka
COPY producer.py ./
CMD ["python", "producer.py"]