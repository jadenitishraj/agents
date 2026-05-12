"""Serialization — what crosses the boundary.

State was designed as a TypedDict (a plain dict at runtime), so
serialization is a one-line change, not a refactor.
"""

from __future__ import annotations

import json

SCHEMA_VERSION = "1.0"


def serialize_trace(trace: dict) -> str:
    """Convert a State dict into a JSON string for disk, network, or audit log."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "trace": dict(trace),
    }
    return json.dumps(payload, indent=2, default=str)


def deserialize_trace(json_str: str) -> dict:
    """Reconstruct a State from its JSON wire format."""
    payload = json.loads(json_str)

    if payload.get("schema_version") != SCHEMA_VERSION:
        print(
            f"Warning: schema version mismatch "
            f"(got {payload.get('schema_version')}, expected {SCHEMA_VERSION})"
        )

    return payload["trace"]
