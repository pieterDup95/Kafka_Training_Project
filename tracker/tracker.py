import json
import os

from confluent_kafka import Consumer, Producer, KafkaError, KafkaException, TopicPartition

consumer_config = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    "group.id": os.getenv("KAFKA_GROUP_ID", "order-tracker"),
    "auto.offset.reset": os.getenv("KAFKA_OFFSET_RESET", "earliest"),
    "enable.auto.commit": False,  # Manual offset management
}

producer_config = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    "enable.idempotence": True,
    "acks": "all",
}

consumer        = Consumer(consumer_config)
producer        = Producer(producer_config)
topic           = os.getenv("KAFKA_TOPIC", "orders")
consumed_topic  = os.getenv("KAFKA_CONSUMED_TOPIC", "order-consumed")
dlt_topic       = os.getenv("KAFKA_DLT_TOPIC", "orders.DLT")

# In-memory store for idempotent processing
processed_orders = set()

consumer.subscribe([topic])
print(f"Consumer running, subscribed to '{topic}', producing confirmations to '{consumed_topic}'")


def delivery_report(err, msg):
    if err:
        print(f"Failed to produce confirmation: {err}")
    else:
        print(f"  Confirmation produced to {msg.topic()} : partition {msg.partition()} : offset {msg.offset()}")


def send_to_dlt(msg, error_message):
    """Send failed message to Dead Letter Topic with enriched headers"""
    try:
        headers = [
            ("original_topic", topic.encode("utf-8")),
            ("original_partition", str(msg.partition()).encode("utf-8")),
            ("original_offset", str(msg.offset()).encode("utf-8")),
            ("error_message", error_message.encode("utf-8")),
        ]

        producer.produce(
            topic=dlt_topic,
            key=msg.key(),
            value=msg.value(),
            headers=headers,
        )
        producer.flush()
        print(f"   Sent to DLT: {error_message}")
    except Exception as e:
        print(f"Failed to send to DLT: {e}")


def process_order(order, msg):
    """Process order with idempotent logic"""
    order_id = order.get("order_id")

    # Idempotent check — prevent duplicate processing
    if order_id in processed_orders:
        print(f"  Order {order_id} already processed, skipping...")
        return True

    # Simulate order processing
    print(f"  Processing order {order_id}...")

    # Build confirmation event
    confirmation = {
        "order_id":          order["order_id"],
        "user":              order["user"],
        "item":              order["item"],
        "quantity":          order["quantity"],
        "status":            "consumed",
        "source_partition":  msg.partition(),
        "source_offset":     msg.offset(),
    }

    # Produce to order-consumed topic
    producer.produce(
        topic=consumed_topic,
        key=order["user"].encode("utf-8"),
        value=json.dumps(confirmation).encode("utf-8"),
        callback=delivery_report
    )
    producer.poll(0)  # Trigger callbacks
    producer.flush()  # Ensure delivery before committing offset

    # Mark as processed
    processed_orders.add(order_id)
    return True


try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            print("Error:", msg.error())
            continue

        try:
            value = msg.value().decode("utf-8")
            order = json.loads(value)
            print(f"Received order: partition={msg.partition()} | offset={msg.offset()} | {order['quantity']} x {order['item']} from {order['user']}")

            # Process order with idempotent logic
            if process_order(order, msg):
                # Commit offset only after successful processing
                consumer.commit(asynchronous=False)
            else:
                print(f"   Processing failed, message will be retried")

        except json.JSONDecodeError as e:
            print(f"Invalid JSON in message: {e}")
            send_to_dlt(msg, f"JSON decode error: {str(e)}")
            consumer.commit(asynchronous=False) 

        except KeyError as e:
            print(f"Missing required field in order: {e}")
            send_to_dlt(msg, f"Missing field: {str(e)}")
            consumer.commit(asynchronous=False) 

        except Exception as e:
            print(f"Unexpected error processing order: {e}")
            send_to_dlt(msg, f"Processing error: {str(e)}")
            consumer.commit(asynchronous=False)

except KeyboardInterrupt:
    print("\nStopping consumer...")

finally:
    producer.flush()   
    consumer.close()
    print("Consumer and producer closed.")