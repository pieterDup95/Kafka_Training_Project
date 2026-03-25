FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir confluent-kafka
COPY tracker.py ./
CMD ["python", "tracker.py"]