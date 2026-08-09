#!/bin/bash

# ============================================================
# Generic node-i3x value reader
#
# Automatically:
#   1. Discovers the i3X model
#   2. Finds the root asset(s)
#   3. Finds all value-bearing properties
#   4. Ignores metadata such as EngineeringUnits / EURange
#   5. Queries all values in one request
#   6. Displays the results
#
# Requirements:
#   - curl
#   - jq
#
# Usage:
#   chmod +x get_i3x_all_values.sh
#   ./get_i3x_all_values.sh
#
# Optional:
#   I3X_URL=http://192.168.1.6:8080 ./get_i3x_all_values.sh
# ============================================================

set -euo pipefail

I3X_URL="${I3X_URL:-http://localhost:8080}"

OBJECTS_URL="${I3X_URL}/v1/objects?includeMetadata=true"
VALUES_URL="${I3X_URL}/v1/objects/value"

echo "=============================================="
echo " Generic node-i3x Reader"
echo "=============================================="
echo
echo "i3X URL: ${I3X_URL}"
echo

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
# Get complete i3X model
# ------------------------------------------------------------

echo "Discovering i3X model..."

OBJECTS=$(curl -fsS "${OBJECTS_URL}")

if ! echo "${OBJECTS}" | jq -e '.success == true' >/dev/null; then
    echo
    echo "ERROR: i3X API did not return success."
    echo "${OBJECTS}" | jq .
    exit 1
fi

NODE_COUNT=$(echo "${OBJECTS}" | jq '.result | length')

echo "Found ${NODE_COUNT} i3X elements."
echo

# ------------------------------------------------------------
# Find root asset(s)
# ------------------------------------------------------------

echo "Root objects:"

echo "${OBJECTS}" | jq -r '
    .result[]
    | select(.parentId == null)
    | "  \(.displayName)\n    \(.elementId)"
'

echo

# ------------------------------------------------------------
# Find all value-bearing properties
#
# A value property:
#
#   elementId starts with "property-"
#
# AND
#
#   its parent is NOT another property
#
# This excludes metadata such as:
#
#   EngineeringUnits
#   EURange
#
# while retaining:
#
#   ChamberTemperature
#   Manufacturer
#   JobId
#   ActiveLayerIndex
#   etc.
# ------------------------------------------------------------

PROPERTIES=$(echo "${OBJECTS}" | jq -c '
    .result as $nodes

    | [
        $nodes[]
        | select(.elementId | startswith("property-"))
        | select(
            .parentId as $parent
            |
            (
                $nodes
                | map(.elementId)
                | index($parent)
            )
            != null
        )
        | select(
            .parentId as $parent
            |
            (
                $nodes
                | map(.elementId)
                | index($parent)
            )
            != null
        )
        | {
            elementId: .elementId,
            displayName: .displayName,
            type: .typeElementId,
            parentId: .parentId,
            engineeringUnit: (.metadata.engUnit // "")
        }
    ]
')

# ------------------------------------------------------------
# Remove properties whose parent is itself a property.
#
# This is the important part that removes:
#
#   EngineeringUnits
#   EURange
#
# while keeping:
#
#   ChamberTemperature
#   SubstrateTemperature
#   AxisXPosition
#   etc.
# ------------------------------------------------------------

VALUE_PROPERTIES=$(echo "${OBJECTS}" | jq -c '
    .result as $nodes

    | [
        $nodes[]
        | select(.elementId | startswith("property-"))
        | . as $property

        | select(
            (
                $nodes[]
                | select(.elementId == $property.parentId)
                | .elementId
            )
            | startswith("property-")
            | not
        )

        | {
            elementId: .elementId,
            displayName: .displayName,
            type: .typeElementId,
            parentId: .parentId,
            engineeringUnit: (.metadata.engUnit // "")
        }
    ]
')

PROPERTY_COUNT=$(echo "${VALUE_PROPERTIES}" | jq 'length')

echo "Found ${PROPERTY_COUNT} value-bearing properties."
echo

if [[ "${PROPERTY_COUNT}" -eq 0 ]]; then
    echo "No value-bearing properties were found."
    exit 0
fi

# ------------------------------------------------------------
# Display discovered properties
# ------------------------------------------------------------

echo "=============================================="
echo " Discovered Values"
echo "=============================================="
echo

echo "${VALUE_PROPERTIES}" | jq -r '
    .[]
    |
    "Name:  \(.displayName)\n" +
    "Type:  \(.type)\n" +
    "Unit:  \(if .engineeringUnit == "" then "-" else .engineeringUnit end)\n" +
    "ID:    \(.elementId)\n"
'

# ------------------------------------------------------------
# Build elementIds array
# ------------------------------------------------------------

ELEMENT_IDS=$(echo "${VALUE_PROPERTIES}" | jq '[.[].elementId]')

VALUES_REQUEST=$(jq -n --argjson ids "${ELEMENT_IDS}" '
    {
        elementIds: $ids
    }
')

# ------------------------------------------------------------
# Query current values
# ------------------------------------------------------------

echo "=============================================="
echo " Reading Current Values"
echo "=============================================="
echo

VALUES=$(curl -fsS \
    -X POST \
    "${VALUES_URL}" \
    -H "Content-Type: application/json" \
    -d "${VALUES_REQUEST}")

# ------------------------------------------------------------
# Verify response
# ------------------------------------------------------------

if ! echo "${VALUES}" | jq -e '.success == true' >/dev/null; then
    echo "ERROR: i3X value query failed."
    echo
    echo "${VALUES}" | jq .
    exit 1
fi

# ------------------------------------------------------------
# Print raw response
# ------------------------------------------------------------

echo "Raw response:"
echo

echo "${VALUES}" | jq .

# ------------------------------------------------------------
# Print a simpler name/value table
#
# The exact value structure can vary by i3X response, so
# first show the raw response above.
# ------------------------------------------------------------

echo
echo "=============================================="
echo " Values by Property"
echo "=============================================="
echo

# Create a lookup table from the returned values.
# We intentionally don't assume a specific nested value
# structure here.
echo "${VALUES}" | jq -r '
    .result[]
    |
    [
        (.elementId // "-"),
        (.value.value // .value // "-")
    ]
    | @tsv
' 2>/dev/null || true

echo
echo "Done."
