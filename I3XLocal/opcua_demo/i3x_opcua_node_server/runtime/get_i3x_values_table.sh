#!/bin/bash

# ============================================================
# node-i3x Generic Value Monitor
#
# Discovers the i3X model dynamically and displays all
# value-bearing properties in a readable table.
#
# Requirements:
#   - curl
#   - jq
#
# Usage:
#   chmod +x get_i3x_values_table.sh
#   ./get_i3x_values_table.sh
#
# Optional:
#   I3X_URL=http://192.168.1.6:8080 ./get_i3x_values_table.sh
#
# Debug:
#   DEBUG=1 ./get_i3x_values_table.sh
# ============================================================

set -euo pipefail

I3X_URL="${I3X_URL:-http://localhost:8080}"

OBJECTS_URL="${I3X_URL}/v1/objects?includeMetadata=true"
VALUES_URL="${I3X_URL}/v1/objects/value"

# ------------------------------------------------------------
# Check dependencies
# ------------------------------------------------------------

if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl is required."
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "ERROR: jq is required."
    echo "Install with:"
    echo "  brew install jq"
    exit 1
fi

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

echo
echo "============================================================"
echo " node-i3x Value Monitor"
echo "============================================================"
echo
echo "Server: ${I3X_URL}"
echo

# ------------------------------------------------------------
# Get model
# ------------------------------------------------------------

OBJECTS=$(curl -fsS "${OBJECTS_URL}")

if ! echo "${OBJECTS}" | jq -e '.success == true' >/dev/null; then
    echo "ERROR: Could not retrieve i3X model."
    echo "${OBJECTS}" | jq .
    exit 1
fi

NODE_COUNT=$(echo "${OBJECTS}" | jq '.result | length')

echo "Discovered ${NODE_COUNT} i3X elements."
echo

# ------------------------------------------------------------
# Find root objects
# ------------------------------------------------------------

echo "Asset(s):"

echo "${OBJECTS}" | jq -r '
    .result[]
    | select(.parentId == null)
    | "  \(.displayName) [\(.elementId)]"
'

echo

# ------------------------------------------------------------
# Build parent lookup
#
# This creates a simple TSV:
#
# elementId    displayName    parentId
#
# We use bash to walk the hierarchy rather than trying to
# make jq perform the recursion.
# ------------------------------------------------------------

declare -A NODE_NAME
declare -A NODE_PARENT
declare -A NODE_TYPE
declare -A NODE_UNIT

while IFS=$'\t' read -r ID NAME PARENT TYPE UNIT; do
    NODE_NAME["$ID"]="$NAME"
    NODE_PARENT["$ID"]="$PARENT"
    NODE_TYPE["$ID"]="$TYPE"
    NODE_UNIT["$ID"]="$UNIT"
done < <(
    echo "${OBJECTS}" | jq -r '
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
    '
)

# ------------------------------------------------------------
# Function:
# Construct the complete hierarchy path for a node.
#
# Example:
#
# AdditiveManufacturingMachine
#   ProcessValues
#     ChamberTemperature
#
# becomes:
#
# AdditiveManufacturingMachine / ProcessValues / ChamberTemperature
# ------------------------------------------------------------

get_path() {

    local ID="$1"
    local PATH=""
    local CURRENT="$ID"

    # Safety limit prevents infinite loops if the model is bad.
    local COUNT=0

    while [[ -n "${CURRENT}" && "${COUNT}" -lt 100 ]]; do

        local NAME="${NODE_NAME[$CURRENT]:-}"

        if [[ -z "${NAME}" ]]; then
            break
        fi

        if [[ -z "${PATH}" ]]; then
            PATH="${NAME}"
        else
            PATH="${NAME} / ${PATH}"
        fi

        CURRENT="${NODE_PARENT[$CURRENT]:-}"

        COUNT=$((COUNT + 1))
    done

    echo "${PATH}"
}

# ------------------------------------------------------------
# Find value-bearing properties
#
# A value-bearing property:
#
#   elementId starts with "property-"
#
# AND its parent is NOT another property.
#
# Therefore:
#
#   ProcessValues / ChamberTemperature       KEEP
#
#   ChamberTemperature / EngineeringUnits   IGNORE
#   ChamberTemperature / EURange             IGNORE
# ------------------------------------------------------------

VALUE_IDS=()

while IFS=$'\t' read -r ID NAME PARENT TYPE UNIT; do

    # Make sure this is a property.
    if [[ "${ID}" != property-* ]]; then
        continue
    fi

    # If the parent is another property, this is metadata.
    PARENT_ID="${NODE_PARENT[$ID]:-}"

    if [[ "${PARENT_ID}" == property-* ]]; then
        continue
    fi

    VALUE_IDS+=("${ID}")

done < <(
    echo "${OBJECTS}" | jq -r '
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
    '
)

echo "Value-bearing properties: ${#VALUE_IDS[@]}"
echo

if [[ "${#VALUE_IDS[@]}" -eq 0 ]]; then
    echo "No value-bearing properties found."
    exit 0
fi

# ------------------------------------------------------------
# Display discovered variables
# ------------------------------------------------------------

echo "============================================================"
echo " Discovered Variables"
echo "============================================================"
echo

printf "%-60s %-12s %-15s\n" \
    "VARIABLE" "UNIT" "TYPE"

printf "%-60s %-12s %-15s\n" \
    "------------------------------------------------------------" \
    "------------" \
    "---------------"

for ID in "${VALUE_IDS[@]}"; do

    NAME="${NODE_NAME[$ID]}"
    TYPE="${NODE_TYPE[$ID]}"
    UNIT="${NODE_UNIT[$ID]:--}"

    PATH=$(get_path "${ID}")

    printf "%-60s %-12s %-15s\n" \
        "${PATH}" \
        "${UNIT}" \
        "${TYPE}"

done

echo

# ------------------------------------------------------------
# Build JSON request
# ------------------------------------------------------------

ELEMENT_IDS_JSON=$(
    printf '%s\n' "${VALUE_IDS[@]}" |
    jq -R . |
    jq -s .
)

REQUEST_BODY=$(jq -n \
    --argjson ids "${ELEMENT_IDS_JSON}" \
    '{
        elementIds: $ids
    }'
)

# ------------------------------------------------------------
# Query values
# ------------------------------------------------------------

echo "Reading current values..."

VALUES=$(curl -fsS \
    -X POST \
    "${VALUES_URL}" \
    -H "Content-Type: application/json" \
    -d "${REQUEST_BODY}")

# ------------------------------------------------------------
# Verify response
# ------------------------------------------------------------

if ! echo "${VALUES}" | jq -e '.success == true' >/dev/null; then
    echo
    echo "ERROR: i3X value query failed."
    echo
    echo "${VALUES}" | jq .
    exit 1
fi

echo "Value query successful."
echo

# ------------------------------------------------------------
# Debug mode
# ------------------------------------------------------------

if [[ "${DEBUG:-0}" == "1" ]]; then

    echo "============================================================"
    echo " DEBUG: Raw Value Response"
    echo "============================================================"
    echo

    echo "${VALUES}" | jq .

    echo

fi

# ------------------------------------------------------------
# Build value lookup
#
# We don't assume too much about the response format.
# The script checks several possible locations for the value.
# ------------------------------------------------------------

declare -A NODE_VALUE

while IFS=$'\t' read -r ID VALUE; do
    NODE_VALUE["$ID"]="$VALUE"
done < <(
    echo "${VALUES}" | jq -r '
        .result[]
        |
        [
            .elementId,

            (
                .value.value
                // .value
                // .dataValue.value.value
                // .dataValue.value
                // "-"
            )
            | tostring
        ]
        | @tsv
    '
)

# ------------------------------------------------------------
# Print current values
# ------------------------------------------------------------

echo "============================================================"
echo " Current Values"
echo "============================================================"
echo

printf "%-55s %-20s %-10s\n" \
    "VARIABLE" "VALUE" "UNIT"

printf "%-55s %-20s %-10s\n" \
    "-------------------------------------------------------" \
    "--------------------" \
    "----------"

for ID in "${VALUE_IDS[@]}"; do

    NAME="${NODE_NAME[$ID]}"
    UNIT="${NODE_UNIT[$ID]:--}"

    PATH=$(get_path "${ID}")
    VALUE="${NODE_VALUE[$ID]:--}"

    printf "%-55s %-20s %-10s\n" \
        "${PATH}" \
        "${VALUE}" \
        "${UNIT}"

done

echo

# ------------------------------------------------------------
# Process values only
# ------------------------------------------------------------

PROCESS_IDS=()

for ID in "${VALUE_IDS[@]}"; do

    PATH=$(get_path "${ID}")

    if [[ "${PATH}" == *" / ProcessValues / "* ]]; then
        PROCESS_IDS+=("${ID}")
    fi

done

if [[ "${#PROCESS_IDS[@]}" -gt 0 ]]; then

    echo "============================================================"
    echo " Process Values"
    echo "============================================================"
    echo

    printf "%-30s %-20s %-10s\n" \
        "VARIABLE" "VALUE" "UNIT"

    printf "%-30s %-20s %-10s\n" \
        "------------------------------" \
        "--------------------" \
        "----------"

    for ID in "${PROCESS_IDS[@]}"; do

        NAME="${NODE_NAME[$ID]}"
        VALUE="${NODE_VALUE[$ID]:--}"
        UNIT="${NODE_UNIT[$ID]:--}"

        printf "%-30s %-20s %-10s\n" \
            "${NAME}" \
            "${VALUE}" \
            "${UNIT}"

    done

    echo

fi

echo "Completed successfully."
echo
