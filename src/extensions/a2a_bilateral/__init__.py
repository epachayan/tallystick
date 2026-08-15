"""Reference implementation: bilateral delegation/execution commitments carried
as an A2A extension. See src/extensions/a2a_bilateral/README.md.

Status: reference library for third-party use, not part of the research
harness. Not scored by make check. The commitment math it calls
(src/crypto/merkle.py) is covered by the project's test suite; the
extension/metadata layer here has its own, separate tests only.
"""

from .card import EXTENSION_URI, extension_descriptor
from .adapter import project_scenario
from .commitment import Commitment, Signer, Verifier, check_assertion, commit, verify_signature
from .metadata import (
    attach_authorization,
    attach_authorization_receipt,
    attach_execution,
    attach_execution_ack,
    extract,
)

__all__ = [
    "EXTENSION_URI",
    "extension_descriptor",
    "project_scenario",
    "Commitment",
    "Signer",
    "Verifier",
    "commit",
    "check_assertion",
    "verify_signature",
    "attach_authorization",
    "attach_authorization_receipt",
    "attach_execution",
    "attach_execution_ack",
    "extract",
]
