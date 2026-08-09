#!/bin/bash

# ============================================================
# node-i3x Generic Value Monitor
#
# macOS / Bash 3.2 compatible
# Designed for Anaconda environments
#
# Requirements:
#   /opt/anaconda3/bin/curl
#   /opt/anaconda3/bin/jq
#
# Usage:
#   bash ./get_i3x_values_mac.sh
#
# Debug:
#   DEBUG=1 bash ./get_i3x_values_mac.sh
# ============================================================

set -euo pipefail

# ============================================================
# Executables
# ============================================================

CURL="/opt/anaconda3/bin/curl"
JQ="/opt/anaconda3/bin/jq"

if [[ ! -x "${CURL}" ]]; then
    echo "ERROR: curl not found at ${CURL}"
    exit 1
fi

if [[ ! -x "${JQ}" ]]; then
    echo "ERROR: jq not found at ${JQ}"
    exit 1
fi

echo "Using curl: ${CURL}"
echo "Using jq:   ${JQ}"

# ============================================================
# Configuration
# ============================================================

I3X_URL="${I3X_URL:-http://localhost:8080}"

OBJECTS_URL="${I3X_URL}/v1/objects?includeMetadata=true"
VALUES_URL="${I3X_URL}/v1/objects/value"

# ============================================================
# Header
# ============================================================

echo
echo "============================================================"
echo " node-i3x Value Monitor"
echo "============================================================"
echo
echo "Server: ${I3X_URL}"
echo

# ============================================================
# Get i3X model
# ============================================================

OBJECTS=$("${CURL}" -fsS "${OBJECTS_URL}")

if ! echo "${OBJECTS}" | "${JQ}" -e '.success == true' >/dev/null; then
    echo "ERROR: Could not retrieve i3X model."
    echo
    echo "${OBJECTS}" | "${JQ}" .
    exit 1
fi

NODE_COUNT=$(echo "${OBJECTS}" | "${JQ}" '.result | length')

echo "Discovered ${NODE_COUNT} i3X elements."
echo

# ============================================================
# Root assets
# ============================================================

echo "Asset(s):"

echo "${OBJECTS}" |
    "${JQ}" -r '
        .result[]
        | select(.parentId == null)
        | "  \(.displayName) [\(.elementId)]"
    '

echo

# ============================================================
# Load model into indexed arrays
#
# Bash 3.2 does not support associative arrays.
# ============================================================

NODE_ID=()
NODE_NAME=()
NODE_PARENT=()
NODE_TYPE=()
NODE_UNIT=()

while IFS=$'\t' read -r ID NAME PARENT TYPE UNIT; do

    NODE_ID[${#NODE_ID[@]}]="${ID}"
    NODE_NAME[${#NODE_NAME[@]}]="${NAME}"
    NODE_PARENT[${#NODE_PARENT[@]}]="${PARENT}"
    NODE_TYPE[${#NODE_TYPE[@]}]="${TYPE}"
    NODE_UNIT[${#NODE_UNIT[@]}]="${UNIT}"

done <<EOF
$(echo "${OBJECTS}" | "${JQ}" -r '
    .result[]
    |
    [
        .elementId,
        .displayName,
        (.parentId // ""),
        (.typeElementId // ""),
        (.metadata.engUnit // "")
    ]
    | @tsv
')
EOF

# ============================================================
# Find array index
# ============================================================

find_index() {

    local SEARCH_ID="$1"
    local i

    for ((i=0; i<${#NODE_ID[@]}; i++)); do

        if [[ "${NODE_ID[$i]}" == "${SEARCH_ID}" ]]; then
            echo "${i}"
            return 0
        fi

    done

    echo "-1"
}

# ============================================================
# Get node name
# ============================================================

get_name() {

    local ID="$1"
    local INDEX

    INDEX=$(find_index "${ID}")

    if [[ "${INDEX}" == "-1" ]]; then
        echo ""
    else
        echo "${NODE_NAME[$INDEX]}"
    fi
}

# ============================================================
# Get node unit
# ============================================================

get_unit() {

    local ID="$1"
    local INDEX

    INDEX=$(find_index "${ID}")

    if [[ "${INDEX}" == "-1" ]]; then
        echo "-"
    elif [[ -n "${NODE_UNIT[$INDEX]}" ]]; then
        echo "${NODE_UNIT[$INDEX]}"
    else
        echo "-"
    fi
}

# ============================================================
# Get node type
# ============================================================

get_type() {

    local ID="$1"
    local INDEX

    INDEX=$(find_index "${ID}")

    if [[ "${INDEX}" == "-1" ]]; then
        echo "-"
    else
        echo "${NODE_TYPE[$INDEX]}"
    fi
}

# ============================================================
# Get parent
# ============================================================

get_parent() {

    local ID="$1"
    local INDEX

    INDEX=$(find_index "${ID}")

    if [[ "${INDEX}" == "-1" ]]; then
        echo ""
    else
        echo "${NODE_PARENT[$INDEX]}"
    fi
}

# ============================================================
# Build hierarchy path
# ============================================================

get_path() {

    local CURRENT="$1"
    local PATH=""
    local COUNT=0

    while [[ -n "${CURRENT}" && "${COUNT}" -lt 100 ]]; do

        NAME=$(get_name "${CURRENT}")

        if [[ -z "${NAME}" ]]; then
            break
        fi

        if [[ -z "${PATH}" ]]; then
            PATH="${NAME}"
        else
            PATH="${NAME} / ${PATH}"
        fi

        CURRENT=$(get_parent "${CURRENT}")

        COUNT=$((COUNT + 1))

    done

    echo "${PATH}"
}

# ============================================================
# Find value-bearing properties
#
# Exclude children such as:
#
#   EngineeringUnits
#   EURange
#
# because their parent is itself a property.
# ============================================================

VALUE_IDS=()

for ((i=0; i<${#NODE_ID[@]}; i++)); do

    ID="${NODE_ID[$i]}"
    PARENT="${NODE_PARENT[$i]}"

    if [[ "${ID}" != property-* ]]; then
        continue
    fi

    if [[ "${PARENT}" == property-* ]]; then
        continue
    fi

    VALUE_IDS[${#VALUE_IDS[@]}]="${ID}"

done

echo "Value-bearing properties: ${#VALUE_IDS[@]}"
echo

# ============================================================
# Discovered Variables
# ============================================================

echo "============================================================"
echo " Discovered Variables"
echo "============================================================"
echo

printf "%-70s %-10s %-15s\n" \
    "VARIABLE" "UNIT" "TYPE"

printf "%-70s %-10s %-15s\n" \
    "----------------------------------------------------------------------" \
    "----------" \
    "---------------"

for ID in "${VALUE_IDS[@]}"; do

    PATH=$(get_path "${ID}")
    UNIT=$(get_unit "${ID}")
    TYPE=$(get_type "${ID}")

    printf "%-70s %-10s %-15s\n" \
        "${PATH}" \
        "${UNIT}" \
        "${TYPE}"

done

echo

# ============================================================
# Build elementIds JSON
# ============================================================

REQUEST_BODY=$(
    printf '%s\n' "${VALUE_IDS[@]}" |
        "${JQ}" -R -s '
            split("\n")
            | map(select(length > 0))
            | {
                elementIds: .
            }
        '
)

if [[ "${DEBUG:-0}" == "1" ]]; then

    echo "============================================================"
    echo " DEBUG: Request Body"
    echo "============================================================"
    echo

    echo "${REQUEST_BODY}" | "${JQ}" .

    echo

fi

# ============================================================
# Query values
# ============================================================

echo "Reading current values..."

VALUES=$(
    "${CURL}" -fsS \
        -X POST \
        "${VALUES_URL}" \
        -H "Content-Type: application/json" \
        -d "${REQUEST_BODY}"
)

echo "Value request completed."
echo

# ============================================================
# Validate response
# ============================================================

if ! echo "${VALUES}" | "${JQ}" -e '.success == true' >/dev/null; then

    echo "ERROR: Value query did not return success."
    echo

    echo "${VALUES}" | "${JQ}" .

    exit 1

fi

# ============================================================
# Always show raw response for now
#
# This is intentional.
#
# Once we see the exact node-i3x v0.9.11 response shape,
# we can make the value display precise.
# ============================================================

echo "============================================================"
echo " Raw Value Response"
echo "============================================================"
echo

echo "${VALUES}" | "${JQ}" .

echo

# ============================================================
# Done
# ============================================================

echo "============================================================"
echo " Model/value query completed"
echo "============================================================"
echo
