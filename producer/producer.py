import json
import uuid
import os

from confluent_kafka import Producer
#from confluent_kafka.admin import AdminClient, NewTopic

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
#admin = AdminClient(producer_config)

def delivery_report(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered {msg.value().decode('utf-8')}")
        print(f"Delivered to {msg.topic()} : partition {msg.partition()} : at offset {msg.offset()}")


def prompt_order():
    print("\n--- New Order ---")
    user = input("Enter username: ").strip()
    item = input("Enter item: ").strip()

    while True:
        try:
            quantity = int(input("Enter quantity: ").strip())
            break
        except ValueError:
            print("Invalid quantity. Please enter a number.")

    return {
        "order_id": str(uuid.uuid4()),
        "user": user,
        "item": item,
        "quantity": quantity
    }


def main():
    topic = os.getenv("KAFKA_TOPIC", "orders")
    print("Order Producer started. Type 'exit' at any prompt to quit.\n")

    while True:
        try:
            user_input = input("Press Enter to create a new order (or type 'exit' to quit): ").strip().lower()
            if user_input == "exit":
                break

            order = prompt_order()

            value = json.dumps(order).encode("utf-8")
            key = order["user"].encode("utf-8") 
            producer.produce(
                topic=topic,
                value=value,
                key=key,
                callback=delivery_report
            )
            producer.flush()

        except KeyboardInterrupt:
            print("\nInterrupted. Exiting...")
            break

    print("Producer shut down.")


if __name__ == "__main__":
    main()
