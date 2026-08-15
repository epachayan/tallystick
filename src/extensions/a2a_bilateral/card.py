"""AgentCard declaration for the bilateral-delegation-commitment extension."""

from __future__ import annotations

# Placeholder. A real deployment mints its own URI it controls; it does not
# need to resolve, it needs to be unique. Do not ship this literal value.
EXTENSION_URI = "https://example.org/ext/bilateral-delegation/v1"


def extension_descriptor(*, required: bool = False, hash_alg: str = "sha256") -> dict:
    """Build the AgentExtension entry for AgentCard.capabilities.extensions.

    See https://github.com/a2aproject/A2A/blob/main/docs/topics/extensions.md
    for the four-field AgentExtension shape (uri, description, required, params)
    this mirrors, and docs/prior-art/a2a-extension-sketch.md in this repository
    for what the extension does and does not resolve.
    """
    return {
        "uri": EXTENSION_URI,
        "description": (
            "Countersigned commitments to authorization scope and execution "
            "record, checkable against a later assertion without disclosing "
            "contents. See tallystick's docs/prior-art/a2a-extension-sketch.md."
        ),
        "required": required,
        "params": {"hashAlg": hash_alg},
    }
