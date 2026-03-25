#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Step 1: Run the Maven build (clean and package)
#mvn clean package -DskipTests

# Step 2: Build the Docker image (if not already handled by docker-compose)

##Build and publish ARM image
nerdctl --namespace k8s.io build -t producer:latest .

kubectl apply -f ../k8s/producer.yaml

kubectl get pods