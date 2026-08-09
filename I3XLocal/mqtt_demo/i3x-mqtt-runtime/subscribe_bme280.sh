#!/bin/bash

CLIENT_ID="mqtt_test_client"
ELEMENT_ID="cesmii_labLA_bme280sensor"

SUB_ID=$(curl -s -X POST http://localhost:8080/subscriptions \
  -H "Content-Type: application/json" \
  -d "{
    \"clientId\": \"$CLIENT_ID\",
    \"displayName\": \"BME280 MQTT Subscription\"
  }" | jq -r '.result.subscriptionId')

echo "Created subscription: $SUB_ID"

curl -s -X POST http://localhost:8080/subscriptions/register \
  -H "Content-Type: application/json" \
  -d "{
    \"clientId\": \"$CLIENT_ID\",
    \"subscriptionId\": \"$SUB_ID\",
    \"elementIds\": [
      \"$ELEMENT_ID\"
    ]
  }" | jq

echo "Starting stream..."

curl -N -X POST http://localhost:8080/subscriptions/stream \
  -H "Content-Type: application/json" \
  -d "{
    \"clientId\": \"$CLIENT_ID\",
    \"subscriptionId\": \"$SUB_ID\"
  }"
