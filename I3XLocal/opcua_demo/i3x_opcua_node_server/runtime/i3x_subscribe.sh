#!/bin/bash

set -euo pipefail

# ============================================================
# node-i3x Subscription Monitor
# ============================================================

I3X_URL="${I3X_URL:-http://localhost:8080}"

# Explicit paths so Anaconda does not interfere with curl.
CURL="${CURL:-/usr/bin/curl}"
JQ="${JQ:-/opt/anaconda3/bin/jq}"

CLIENT_ID="${CLIENT_ID:-mac-test-$$}"
DISPLAY_NAME="${DISPLAY_NAME:-Mac i3X Subscription Test}"

echo
echo "============================================================"
echo " node-i3x Subscription Monitor"
echo "============================================================"
echo
echo "Server:    $I3X_URL"
echo "Client ID: $CLIENT_ID"
echo "curl:      $CURL"
echo "jq:        $JQ"
echo

# ------------------------------------------------------------
# Check dependencies
# ------------------------------------------------------------

if [ ! -x "$CURL" ]; then
    echo "ERROR: curl not found at $CURL"
    echo
    echo "Try:"
    echo "  which curl"
    exit 1
fi

if [ ! -x "$JQ" ]; then
    echo "ERROR: jq not found at $JQ"
    echo
    echo "Try:"
    echo "  which jq"
    exit 1
fi

# ------------------------------------------------------------
# Create subscription
# ------------------------------------------------------------

echo "Creating subscription..."

CREATE_RESPONSE="$("$CURL" -sS -X POST \
    "$I3X_URL/v1/subscriptions" \
    -H "Content-Type: application/json" \
    -d "{
        \"clientId\": \"$CLIENT_ID\",
        \"displayName\": \"$DISPLAY_NAME\"
    }")"

echo
echo "Subscription response:"
echo "$CREATE_RESPONSE" | "$JQ" .

# Check success
CREATE_SUCCESS=$(echo "$CREATE_RESPONSE" | "$JQ" -r '.success // false')

if [ "$CREATE_SUCCESS" != "true" ]; then
    echo
    echo "ERROR: Subscription creation failed."
    exit 1
fi

# ------------------------------------------------------------
# Extract subscription ID
# ------------------------------------------------------------

SUBSCRIPTION_ID=$(echo "$CREATE_RESPONSE" | "$JQ" -r '
    .result.subscriptionId //
    .result.id //
    empty
')

if [ -z "$SUBSCRIPTION_ID" ]; then
    echo
    echo "ERROR: Could not find subscriptionId in response."
    echo
    echo "$CREATE_RESPONSE" | "$JQ" .
    exit 1
fi

echo
echo "Subscription created successfully."
echo
echo "  Client ID:       $CLIENT_ID"
echo "  Subscription ID: $SUBSCRIPTION_ID"
echo

# ------------------------------------------------------------
# Variables to subscribe to
# ------------------------------------------------------------

ELEMENT_IDS=(
    "property-b58377c97a346ba0-additivemanufacturingmachine-processvalues-chambertemperature"
    "property-b58377c97a346ba0-additivemanufacturingmachine-processvalues-substratetemperature"
    "property-b58377c97a346ba0-additivemanufacturingmachine-processvalues-axisxposition"
    "property-b58377c97a346ba0-additivemanufacturingmachine-processvalues-recoaterspeed"
    "property-b58377c97a346ba0-additivemanufacturingmachine-processvalues-laserpoweroutput"
    "property-b58377c97a346ba0-additivemanufacturingmachine-processvalues-shieldinggaspressure"
    "property-b58377c97a346ba0-additivemanufacturingmachine-processvalues-powderlevelpercentage"
)

# ------------------------------------------------------------
# Build registration JSON
# ------------------------------------------------------------

ELEMENT_JSON=$(
    printf '%s\n' "${ELEMENT_IDS[@]}" |
    "$JQ" -R . |
    "$JQ" -s .
)

REGISTER_PAYLOAD=$(
    "$JQ" -n \
        --arg clientId "$CLIENT_ID" \
        --arg subscriptionId "$SUBSCRIPTION_ID" \
        --argjson elementIds "$ELEMENT_JSON" \
        '{
            clientId: $clientId,
            subscriptionId: $subscriptionId,
            elementIds: $elementIds
        }'
)

# ------------------------------------------------------------
# Register variables
# ------------------------------------------------------------

echo "Registering ProcessValues variables..."

REGISTER_RESPONSE="$("$CURL" -sS -X POST \
    "$I3X_URL/v1/subscriptions/register" \
    -H "Content-Type: application/json" \
    -d "$REGISTER_PAYLOAD")"

echo
echo "Registration response:"
echo "$REGISTER_RESPONSE" | "$JQ" .

REGISTER_SUCCESS=$(echo "$REGISTER_RESPONSE" | "$JQ" -r '.success // false')

if [ "$REGISTER_SUCCESS" != "true" ]; then
    echo
    echo "ERROR: Variable registration failed."
    exit 1
fi

echo
echo "Registration successful."
echo
echo "Variables:"
echo "  - ChamberTemperature"
echo "  - SubstrateTemperature"
echo "  - AxisXPosition"
echo "  - RecoaterSpeed"
echo "  - LaserPowerOutput"
echo "  - ShieldingGasPressure"
echo "  - PowderLevelPercentage"
echo

# ------------------------------------------------------------
# Start SSE stream
# ------------------------------------------------------------

echo "============================================================"
echo " Starting SSE stream"
echo "============================================================"
echo
echo "Press Ctrl+C to stop."
echo

"$CURL" -N -sS -X POST \
    "$I3X_URL/v1/subscriptions/stream" \
    -H "Content-Type: application/json" \
    -H "Accept: text/event-stream" \
    -d "{
        \"clientId\": \"$CLIENT_ID\",
        \"subscriptionId\": \"$SUBSCRIPTION_ID\"
    }"
