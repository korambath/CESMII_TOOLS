#!/bin/bash

# node-i3x process variable reader
#
# Requirements:
#   - curl
#   - jq
#   - node-i3x running on localhost:8080
#
# Usage:
#   chmod +x get_i3x_values.sh
#   ./get_i3x_values.sh
#
# Optional:
#   I3X_URL=http://192.168.1.6:8080 ./get_i3x_values.sh

set -euo pipefail

I3X_URL="${I3X_URL:-http://localhost:8080}"

OBJECTS_URL="${I3X_URL}/v1/objects?includeMetadata=true"
VALUES_URL="${I3X_URL}/v1/objects/value"

echo "Connecting to: ${I3X_URL}"
echo

# ------------------------------------------------------------
# Get all objects/elements
# ------------------------------------------------------------

OBJECTS=$(curl -fsS "${OBJECTS_URL}")

# Verify the API returned success
if ! echo "${OBJECTS}" | jq -e '.success == true' >/dev/null; then
    echo "ERROR: i3X API did not return success."
    echo "${OBJECTS}" | jq .
    exit 1
fi

# ------------------------------------------------------------
# Find the root asset
#
# We identify it as the object with:
#   parentId == null
# ------------------------------------------------------------

ASSET=$(echo "${OBJECTS}" | jq -r '
    .result[]
    | select(.parentId == null)
    | select(.isComposition == true)
    | .elementId
' | head -n 1)

if [[ -z "${ASSET}" || "${ASSET}" == "null" ]]; then
    echo "ERROR: Could not find root asset."
    exit 1
fi

ASSET_NAME=$(echo "${OBJECTS}" | jq -r --arg id "${ASSET}" '
    .result[]
    | select(.elementId == $id)
    | .displayName
')

echo "Asset:"
echo "  Name: ${ASSET_NAME}"
echo "  ID:   ${ASSET}"
echo

# ------------------------------------------------------------
# Find ProcessValues object
# ------------------------------------------------------------

PROCESS_VALUES=$(echo "${OBJECTS}" | jq -r --arg asset "${ASSET}" '
    .result[]
    | select(.parentId == $asset)
    | select(.displayName == "ProcessValues")
    | .elementId
' | head -n 1)

if [[ -z "${PROCESS_VALUES}" || "${PROCESS_VALUES}" == "null" ]]; then
    echo "ERROR: Could not find ProcessValues under ${ASSET_NAME}."
    exit 1
fi

echo "ProcessValues:"
echo "  ID: ${PROCESS_VALUES}"
echo

# ------------------------------------------------------------
# Find all properties directly underneath ProcessValues
# ------------------------------------------------------------

PROPERTIES=$(echo "${OBJECTS}" | jq -c --arg parent "${PROCESS_VALUES}" '
    [
        .result[]
        | select(.parentId == $parent)
        | select(.elementId | startswith("property-"))
        | {
            elementId: .elementId,
            displayName: .displayName,
            type: .typeElementId,
            engineeringUnit: (.metadata.engUnit // "")
        }
    ]
')

PROPERTY_COUNT=$(echo "${PROPERTIES}" | jq 'length')

if [[ "${PROPERTY_COUNT}" -eq 0 ]]; then
    echo "ERROR: No process variables found."
    exit 1
fi

echo "Found ${PROPERTY_COUNT} process variables:"
echo

echo "${PROPERTIES}" | jq -r '
    .[]
    | "  \(.displayName) [\(.engineeringUnit)]"
'

echo
echo "Reading current values..."
echo

# ------------------------------------------------------------
# Build the elementIds array and query values
# ------------------------------------------------------------

ELEMENT_IDS=$(echo "${PROPERTIES}" | jq -c '[.[].elementId]')

VALUES_REQUEST=$(jq -n --argjson ids "${ELEMENT_IDS}" '
    {
        elementIds: $ids
    }
')

VALUES=$(curl -fsS \
    -X POST \
    "${VALUES_URL}" \
    -H "Content-Type: application/json" \
    -d "${VALUES_REQUEST}")

# ------------------------------------------------------------
# Display the returned values
# ------------------------------------------------------------

echo "=============================================="
echo " i3X Process Values"
echo "=============================================="
echo

echo "${VALUES}" | jq .
