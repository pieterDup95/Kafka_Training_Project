import json
import os

from confluent_kafka import Consumer

consumer_config = {
     "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    "group.id": os.getenv("KAFKA_GROUP_ID", "order-tracker"),
    "auto.offset.reset": os.getenv("KAFKA_OFFSET_RESET", "earliest")
}

consumer = Consumer(consumer_config)
topic = os.getenv("KAFKA_TOPIC", "orders")
consumer.subscribe([topic])

print(f"Consumer running, subscribed to {topic}")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(" Error:", msg.error())
            continue

        value = msg.value().decode("utf-8")
        order = json.loads(value)
        print(f"Received order: {order['quantity']} x {order['item']} from {order['user']}")

except KeyboardInterrupt:
    print("\nStopping consumer")

finally:
    consumer.close()