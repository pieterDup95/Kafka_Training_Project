# Deployment Guide

This guide provides the correct deployment order for the multi-broker Kafka order processing platform on Kubernetes.

## Prerequisites

- Kubernetes cluster (Rancher Desktop)
- kubectl configured
- Docker for building images

## Deployment Order

Components must be deployed in the following order to avoid dependency failures:

### 1. Deploy Kafka StatefulSet and Services

```bash
kubectl apply -f k8s/advanced/kafka-statefulset.yaml
```

This creates:
- `kafka-headless` service 
- `kafka-service` service 
- 3-broker Kafka StatefulSet with KRaft mode

### 2. Wait for Kafka Brokers to be Ready

```bash
kubectl wait --for=condition=ready pod -l app=kafka --timeout=300s
```

Verify all 3 brokers are running:
```bash
kubectl get pods -l app=kafka
```

### 3. Initialize Topics

```bash
kubectl apply -f k8s/advanced/kafka-topic-job.yaml
```

Wait for job completion:
```bash
kubectl wait --for=condition=complete job/kafka-topic-init --timeout=120s
```

Verify topics created:
```bash
kubectl logs job/kafka-topic-init
```

This creates three topics:
- `orders` [3 partitions, 7 day retention]
- `order-consumed` [3 partitions, 3 day retention]
- `orders.DLT` [3 partitions, 30 day retention]

### 4. Build and Deploy Order Consumer

Build the consumer image:
```bash
cd tracker
./deploy.sh
cd ..
```
If this fails, run the commands in deploy.sh seperatly.


Verify consumers are running:
```bash
kubectl get pods -l app=order-consumer
kubectl logs -l app=order-consumer -f
```

### 5. Build and Run Order Producer

Build the auto-producer image:
```bash
cd auto-producer
./deploy.sh
cd ..
```
If this fails, run the commands in deploy.sh seperatly.


Monitor producer progress:
```bash
kubectl logs -f job/auto-producer
```

The job will automatically clean up 60 seconds after completion.

### 6. Deploy Kafka UI

```bash
kubectl apply -f k8s/advanced/kafkaUI.yaml
```



## Verification

### Check topic creation
```bash
kubectl exec -it kafka-0 -- kafka-topics --bootstrap-server localhost:9092 --list
```

### Check consumer group offsets
```bash
kubectl exec -it kafka-0 -- kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group order-tracker
```

### View messages in order-consumed topic
```bash
kubectl exec -it kafka-0 -- kafka-console-consumer --bootstrap-server localhost:9092 --topic order-consumed --from-beginning --max-messages 10
```

### View Dead Letter Topic
```bash
kubectl exec -it kafka-0 -- kafka-console-consumer --bootstrap-server localhost:9092 --topic orders.DLT --from-beginning --property print.headers=true
```

## Safe Event Replay

To replay events without affecting the consumer group:

1. **Update the consumer group ID** in `k8s/replay-consumer.yaml`:
   ```yaml
   - name: KAFKA_GROUP_ID
     value: "order-tracker-replay-2026-03-26-<timestamp>"  # Use current timestamp
   ```

2. **Deploy the replay job**:
   ```bash
   kubectl apply -f k8s/replay-consumer.yaml
   ```

3. **Monitor replay progress**:
   ```bash
   kubectl logs -f job/replay-consumer
   ```

4. **Clean up when done**:
   ```bash
   kubectl delete job replay-consumer
   ```

The replay consumer will:
- Use a unique consumer group ID (does not affect production offsets)
- Reprocess all messages from the beginning
- Skip already-processed order_ids (idempotent)
- Emit confirmation events to order-consumed
- Run as a Job and complete when caught up (requires SIGTERM handling)
