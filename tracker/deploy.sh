#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Step 1: Run the Maven build (clean and package)
#mvn clean package -DskipTests

# Step 2: Build the Docker image (if not already handled by docker-compose)

##Build and publish ARM imagekub

#  export KUBECONFIG="/mnt/c/Users/CP375007/.kube/config"


nerdctl --namespace k8s.io build -t tracker:latest .

kubectl apply -f ../k8s/tracker-deployment.yaml

kubectl get pods




