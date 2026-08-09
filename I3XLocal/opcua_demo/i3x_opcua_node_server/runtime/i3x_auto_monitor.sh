#!/bin/bash

set -uo pipefail

# ============================================================
# node-i3x Generic Live Value Monitor
# macOS
#
# Discovers:
#   /v1/objects
#
# Creates:
#   /v1/subscriptions
#
# Registers:
#   /v1/subscriptions/register
#
# Streams:
#   /v1/subscriptions/stream
# ============================================================

I3X_URL="${I3X_URL:-http://localhost:8080}"

# Prefer native macOS curl.
CURL="${CURL:-/usr/bin/curl}"

# jq location can be overridden:
#   JQ=/usr/local/bin/jq ./i3x_auto_monitor.sh
JQ="${JQ:-/opt/anaconda3/bin/jq}"

CLIENT_ID="${CLIENT_ID:-mac-auto-monitor-$$}"
DISPLAY_NAME="${DISPLAY_NAME:-Generic i3X Live Monitor}"

echo "Using curl: $CURL"
echo "Using jq:   $JQ"
echo

# ============================================================
# Dependencies
# ============================================================

if [ ! -x "$CURL" ]; then
    echo "ERROR: curl not found: $CURL"
    exit 1
fi

if [ ! -x "$JQ" ]; then
    echo "ERROR: jq not found: $JQ"
    exit 1
fi

echo "============================================================"
echo " Generic node-i3x Live Value Monitor"
echo "============================================================"
echo
echo "Server: $I3X_URL"
echo

# ============================================================
# Discover model
# ============================================================

echo "Discovering i3X model..."

OBJECTS_RESPONSE="$(
    "$CURL" -sS \
        "$I3X_URL/v1/objects?includeMetadata=true"
)"

if ! echo "$OBJECTS_RESPONSE" | "$JQ" -e '.success == true' >/dev/null 2>&1; then
    echo
    echo "ERROR: Could not retrieve i3X model."
    echo "$OBJECTS_RESPONSE" | "$JQ" .
    exit 1
fi

MODEL_FILE="$(mktemp)"
PROPERTY_FILE="$(mktemp)"
LOOKUP_FILE="$(mktemp)"

cleanup() {
    rm -f "$MODEL_FILE" "$PROPERTY_FILE" "$LOOKUP_FILE"
}

trap cleanup EXIT INT TERM

echo "$OBJECTS_RESPONSE" | "$JQ" '.result' > "$MODEL_FILE"

OBJECT_COUNT="$("$JQ" 'length' "$MODEL_FILE")"

echo "Discovered $OBJECT_COUNT i3X elements."
echo

# ============================================================
# Root objects
# ============================================================

echo "Root objects:"

"$JQ" -r '
    .[]
    | select(
        .parentId == null
        and .isComposition == true
    )
    | "  \(.displayName) [\(.elementId)]"
' "$MODEL_FILE"

echo

# ============================================================
# Find value-bearing properties
#
# Actual data properties have an asset/object parent.
# Metadata children such as EngineeringUnits/EURange have
# another property as their parent and are excluded.
# ============================================================

"$JQ" '
[
    .[]
    | select(
        (.elementId | startswith("property-"))
        and
        (.parentId | startswith("asset-"))
    )
]
' "$MODEL_FILE" > "$PROPERTY_FILE"

PROPERTY_COUNT="$("$JQ" 'length' "$PROPERTY_FILE")"

echo "Value-bearing properties: $PROPERTY_COUNT"
echo

# ============================================================
# Build hierarchy path
# ============================================================

get_path() {
    local id="$1"

    "$JQ" -r --arg id "$id" '
        def node($id):
            .[] | select(.elementId == $id);

        def buildpath($id):
            node($id) as $n
            |
            if $n.parentId == null then
                [$n.displayName]
            else
                (buildpath($n.parentId) + [$n.displayName])
            end;

        buildpath($id) | join(" / ")
    ' "$MODEL_FILE"
}

# ============================================================
# Display discovered variables
# ============================================================

echo "============================================================"
echo " Discovered Variables"
echo "============================================================"
echo

printf "%-65s %-12s %-12s\n" \
    "VARIABLE" "UNIT" "TYPE"

printf "%-65s %-12s %-12s\n" \
    "-----------------------------------------------------------------" \
    "------------" \
    "------------"

while IFS= read -r property; do

    ELEMENT_ID="$(
        echo "$property" |
        "$JQ" -r '.elementId'
    )"

    TYPE="$(
        echo "$property" |
        "$JQ" -r '.typeElementId'
    )"

    UNIT="$(
        echo "$property" |
        "$JQ" -r '.metadata.engUnit // "-"'
    )"

    PATH_NAME="$(get_path "$ELEMENT_ID")"

    printf "%-65s %-12s %-12s\n" \
        "$PATH_NAME" \
        "$UNIT" \
        "$TYPE"

done < <("$JQ" -c '.[]' "$PROPERTY_FILE")

echo

# ============================================================
# Build element ID array
# ============================================================

ELEMENT_IDS="$(
    "$JQ" '[.[].elementId]' "$PROPERTY_FILE"
)"

# ============================================================
# Create subscription
# ============================================================

echo "Creating subscription..."

CREATE_RESPONSE="$(
    "$CURL" -sS \
        -X POST \
        "$I3X_URL/v1/subscriptions" \
        -H "Content-Type: application/json" \
        -d "{
            \"clientId\": \"$CLIENT_ID\",
            \"displayName\": \"$DISPLAY_NAME\"
        }"
)"

if ! echo "$CREATE_RESPONSE" |
    "$JQ" -e '.success == true' >/dev/null 2>&1
then
    echo
    echo "ERROR: Subscription creation failed."
    echo "$CREATE_RESPONSE" | "$JQ" .
    exit 1
fi

SUBSCRIPTION_ID="$(
    echo "$CREATE_RESPONSE" |
    "$JQ" -r '
        .result.subscriptionId //
        .result.id //
        .subscriptionId //
        empty
    '
)"

if [ -z "$SUBSCRIPTION_ID" ]; then
    echo
    echo "ERROR: Could not find subscription ID."
    echo "$CREATE_RESPONSE" | "$JQ" .
    exit 1
fi

echo "Subscription ID: $SUBSCRIPTION_ID"
echo

# ============================================================
# Register variables
# ============================================================

echo "Registering $PROPERTY_COUNT variables..."

REGISTER_PAYLOAD="$(
    "$JQ" -n \
        --arg clientId "$CLIENT_ID" \
        --arg subscriptionId "$SUBSCRIPTION_ID" \
        --argjson elementIds "$ELEMENT_IDS" '
        {
            clientId: $clientId,
            subscriptionId: $subscriptionId,
            elementIds: $elementIds
        }
        '
)"

REGISTER_RESPONSE="$(
    "$CURL" -sS \
        -X POST \
        "$I3X_URL/v1/subscriptions/register" \
        -H "Content-Type: application/json" \
        -d "$REGISTER_PAYLOAD"
)"

if ! echo "$REGISTER_RESPONSE" |
    "$JQ" -e '.success == true' >/dev/null 2>&1
then
    echo
    echo "ERROR: Registration failed."
    echo "$REGISTER_RESPONSE" | "$JQ" .
    exit 1
fi

echo "Registration successful."
echo

# ============================================================
# Build lookup file
#
# IMPORTANT:
# This is JSONL -- one JSON object per line.
# ============================================================

while IFS= read -r property; do

    ELEMENT_ID="$(
        echo "$property" |
        "$JQ" -r '.elementId'
    )"

    DISPLAY_NAME="$(
        echo "$property" |
        "$JQ" -r '.displayName'
    )"

    UNIT="$(
        echo "$property" |
        "$JQ" -r '.metadata.engUnit // "-"'
    )"

    PATH_NAME="$(get_path "$ELEMENT_ID")"

    "$JQ" -cn \
        --arg id "$ELEMENT_ID" \
        --arg name "$DISPLAY_NAME" \
        --arg path "$PATH_NAME" \
        --arg unit "$UNIT" '
        {
            elementId: $id,
            displayName: $name,
            path: $path,
            unit: $unit
        }
        ' >> "$LOOKUP_FILE"

done < <("$JQ" -c '.[]' "$PROPERTY_FILE")

# ============================================================
# Helper: find variable information
# ============================================================

lookup_variable() {
    local id="$1"

    "$JQ" -r \
        --arg id "$id" '
        select(.elementId == $id)
        | [.path, .unit]
        | @tsv
    ' "$LOOKUP_FILE" |
    head -n 1
}

# ============================================================
# Start SSE stream
# ============================================================

echo
echo "============================================================"
echo " LIVE i3X STREAM"
echo "============================================================"
echo
echo "Subscription: $SUBSCRIPTION_ID"
echo "Variables:    $PROPERTY_COUNT"
echo
echo "Press Ctrl+C to stop."
echo

printf "%-24s %-65s %-20s\n" \
    "TIME" "VARIABLE" "VALUE"

printf "%-24s %-65s %-20s\n" \
    "------------------------" \
    "-----------------------------------------------------------------" \
    "--------------------"

# ============================================================
# SSE stream
#
# Do NOT pipe curl directly into a fragile jq chain.
# First capture each complete "data:" line and then inspect it.
# ============================================================

"$CURL" -N -sS \
    -X POST \
    "$I3X_URL/v1/subscriptions/stream" \
    -H "Content-Type: application/json" \
    -H "Accept: text/event-stream" \
    -d "{
        \"clientId\": \"$CLIENT_ID\",
        \"subscriptionId\": \"$SUBSCRIPTION_ID\"
    }" |
while IFS= read -r line; do

    # --------------------------------------------------------
    # Only process SSE data lines.
    # --------------------------------------------------------

    case "$line" in

        data:\ *)

            DATA="${line#data: }"

            # ------------------------------------------------
            # Validate JSON.
            # ------------------------------------------------

            if ! echo "$DATA" |
                "$JQ" -e . >/dev/null 2>&1
            then
                echo
                echo "Raw SSE data:"
                echo "$DATA"
                echo
                continue
            fi

            # ------------------------------------------------
            # DEBUG / discovery of actual stream structure.
            #
            # We support:
            #
            #   { elementId: ..., value: ... }
            #
            #   { result: { elementId: ..., value: ... } }
            #
            #   { data: { elementId: ..., value: ... } }
            #
            #   [ { elementId: ..., value: ... }, ... ]
            #
            #   { results: [...] }
            # ------------------------------------------------

            EVENTS="$(
                echo "$DATA" |
                "$JQ" -c '
                    if type == "array" then
                        .[]
                    elif (.results? | type) == "array" then
                        .results[]
                    elif (.result? | type) == "array" then
                        .result[]
                    elif (.data? | type) == "array" then
                        .data[]
                    else
                        .
                    end
                '
            )"

            while IFS= read -r EVENT; do

                [ -z "$EVENT" ] && continue

                # ------------------------------------------------
                # Extract element ID.
                # ------------------------------------------------

                ELEMENT_ID="$(
                    echo "$EVENT" |
                    "$JQ" -r '
                        .elementId //
                        .result.elementId //
                        .data.elementId //
                        empty
                    '
                )"

                # ------------------------------------------------
                # If this event is not a value event, show it.
                # ------------------------------------------------

                if [ -z "$ELEMENT_ID" ]; then
                    echo
                    echo "SSE event:"
                    echo "$EVENT" | "$JQ" .
                    echo
                    continue
                fi

                # ------------------------------------------------
                # Extract value.
                # ------------------------------------------------

                VALUE="$(
                    echo "$EVENT" |
                    "$JQ" -c '
                        if has("value") then
                            .value
                        elif (.result? | type) == "object" and
                             (.result | has("value")) then
                            .result.value
                        elif (.data? | type) == "object" and
                             (.data | has("value")) then
                            .data.value
                        else
                            null
                        end
                    '
                )"

                # ------------------------------------------------
                # Extract timestamp.
                # ------------------------------------------------

                TIMESTAMP="$(
                    echo "$EVENT" |
                    "$JQ" -r '
                        .timestamp //
                        .result.timestamp //
                        .data.timestamp //
                        empty
                    '
                )"

                # ------------------------------------------------
                # Look up friendly name.
                # ------------------------------------------------

                INFO="$(lookup_variable "$ELEMENT_ID")"

                if [ -n "$INFO" ]; then

                    VARIABLE_PATH="$(printf '%s\n' "$INFO" | cut -f1)"
                    UNIT="$(printf '%s\n' "$INFO" | cut -f2)"

                else

                    VARIABLE_PATH="$ELEMENT_ID"
                    UNIT="-"

                fi

                # ------------------------------------------------
                # Time.
                # ------------------------------------------------

                if [ -n "$TIMESTAMP" ]; then
                    DISPLAY_TIME="$TIMESTAMP"
                else
                    DISPLAY_TIME="$(date '+%Y-%m-%d %H:%M:%S')"
                fi

                # ------------------------------------------------
                # Pretty value.
                # ------------------------------------------------

                if [ "$VALUE" = "null" ]; then
                    DISPLAY_VALUE="null"
                else
                    DISPLAY_VALUE="$(
                        echo "$VALUE" |
                        "$JQ" -r '
                            if type == "string" then
                                .
                            else
                                tostring
                            end
                        '
                    )"
                fi

                printf "%-24s %-65s %-20s\n" \
                    "$DISPLAY_TIME" \
                    "$VARIABLE_PATH" \
                    "$DISPLAY_VALUE $UNIT"

            done <<< "$EVENTS"

            ;;

        event:\ *)
            # SSE event name.
            ;;

        id:\ *)
            # SSE event ID.
            ;;

        retry:\ *)
            # SSE reconnect instruction.
            ;;

        :)
            # SSE keep-alive.
            ;;

        "")
            # Blank line terminates an SSE event.
            ;;

        *)
            # Ignore other SSE protocol lines.
            ;;

    esac

done

echo
echo "Stream ended."
