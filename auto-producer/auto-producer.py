import json
import uuid
import os
import time
import random

from confluent_kafka import Producer

producer_config = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092"),
    "enable.idempotence": True,
    "acks": "all",
    "retries": 10,
    "retry.backoff.ms": 500,
    "delivery.timeout.ms": 30000,
    "max.in.flight.requests.per.connection": 5,
}

producer = Producer(producer_config)

USERS  = ["lara", "john", "sara", "mike", "amy"]
ITEMS  = ["frozen yogurt", "ice cream", "coffee", "sandwich", "juice"]

delivered     = 0
failed        = 0

def delivery_report(err, msg):
    global delivered, failed
    if err:
        failed += 1
        print(f"Delivery failed: {err}")
    else:
        delivered += 1
        print(f"[{delivered}/100] Delivered to {msg.topic()} : partition {msg.partition()} : offset {msg.offset()}")


def generate_order():
    return {
        "order_id": str(uuid.uuid4()),
        "user":     random.choice(USERS),
        "item":     random.choice(ITEMS),
        "quantity": random.randint(1, 20)
    }


def main():
    topic       = os.getenv("KAFKA_TOPIC", "orders")
    num_events  = 100

    print(f"Producing {num_events} orders to topic '{topic}'...\n")

    start_time = time.time()  # start timer

    for i in range(num_events):
        order = generate_order()
        value = json.dumps(order).encode("utf-8")
        key   = order["user"].encode("utf-8")

        producer.produce(
            topic=topic,
            value=value,
            key=key,
            callback=delivery_report
        )
        producer.poll(0)  # non-blocking — triggers callbacks without waiting

    print("\nAll 100 events queued. Waiting for delivery confirmations...\n")
    producer.flush()      # blocks until all delivered

    end_time = time.time()  # end timer

    duration = end_time - start_time

    print(f"\n--- Results ---")
    print(f"Total events produced : {num_events}")
    print(f"Successfully delivered : {delivered}")
    print(f"Failed                : {failed}")
    print(f"Time taken            : {duration:.3f} seconds")
    print(f"Throughput            : {num_events / duration:.1f} events/sec")


if __name__ == "__main__":
    main()
 