#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# # Configure Zscaler certificate for kubectl/kuberlr
# export SSL_CERT_FILE="$(pwd)/ZscalerRootCertificate-2048-SHA256.crt"
# export CURL_CA_BUNDLE="$(pwd)/ZscalerRootCertificate-2048-SHA256.crt"

# # Configure Zscaler certificate for kubectl/kuberlr
# export SSL_CERT_FILE="$(pwd)/ZscalerRootCertificate-2048-SHA256.crt"
# export CURL_CA_BUNDLE="$(pwd)/ZscalerRootCertificate-2048-SHA256.crt"

# # # Set KUBECONFIG - use WSL path format
#  export KUBECONFIG="/mnt/c/Users/CP375007/.kube/config"

# # Step 1: Run the Maven build (clean and package)
# #mvn clean package -DskipTests

# # Step 2: Build the Docker image (if not already handled by docker-compose)

# ##Build and publish ARM image
# nerdctl --namespace k8s.io build -t producer:latest .

# kubectl apply -f ../k8s/producer.yaml --validate=false

# kubectl get pods



 export KUBECONFIG="/mnt/c/Users/CP375007/.kube/config"
 nerdctl --namespace k8s.io build -t auto-producer:latest .

kubectl apply -f ../k8s/auto-producer.yaml

kubectl get pods