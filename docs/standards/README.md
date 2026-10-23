# Agent-protocol mapping study: evidence under dispute

**Status:** unscored research design, 23 October 2026. This document does **not** claim conformance to any cited Internet-Draft, and no draft results have been obtained.

This study maps three version-pinned individual Internet-Drafts to Tallystick's three-party dispute model (P → I → E). The intended deliverable is a **defensible evidence-projection comparison**, not a score table inferred from prose. The attached TOML files are **mapping manifests**, not Tallystick executable protocol specifications; they deliberately sit outside `specs/`.

## The architectural obstacle

A Tallystick protocol is not added merely by writing a TOML file:

1. `src/multihop/spec.py` fixes `SPEC_NAMES = ("bearer3", "hop3", "chain3")` and defines a message as `from`, `to`, `signed`, `binds`, `forwards`, `requires`, and `checks`.
2. `src/multihop/protocols.py` separately registers the adjudicator and disclosure mode.
3. `src/multihop/generator.py` emits a fixed `FLOW` of seven message names and objects `G`, `S`, `X`, `R`.
4. `read_evidence` currently interprets these objects using assumptions particular to the original three-party study.
5. Conformance and boundary declarations (including expected prevention and twins), the generated protocol document, and the two-party freeze must remain consistent.

Most importantly, `Message.signed` means the **sender** signed. That cannot faithfully express a message transported by an intermediary but signed by a different issuer, as HDP v0.1 does. Nor can set equality/subset checks model clock time, revocation, identity-key binding, real signed wire payloads, or an external policy gate.

## Pinned drafts and initial evidence mapping

| Draft | Version | What it commits to | What the current model misses | Initial disposition |
|---|---|---|---|---|
| Agent Delegation Receipts | `draft-nelson-agent-delegation-receipts-15` (21 Oct) | Signed authorization envelope, narrower sub-receipts, holder-binding, pre-execution verification profile | Key custody; per-action gate decisions and observations; time and revocation; instruction hashes; separation from external content profiles | Partial authorization projection possible; **not scored** |
| XAIP execution receipts | `draft-xkumakichi-xaip-receipts-03` (2 Jul) | Agent-signed per-call facts, optional caller co-signature | Independent observation; dual signatures on identical payload; receipt fields and hashing; delivery/custody policy | Partial receipt projection possible; **not scored** |
| Human Delegation Provenance | `draft-helixar-hdp-agentic-delegation-03` (6 Oct) | Issuer-signed root and issuer-signed cumulative delegation hops; provenance, *not* authorization | Separate issuer role/signing identity, cumulative signed chain, truncation and off-record actions | Blocked on model extension; **not scored** |

All three are *individual Internet-Drafts*, not adopted IETF standards. Their specifications evolve; compare only the pinned revisions.

Sources:
- https://datatracker.ietf.org/doc/html/draft-nelson-agent-delegation-receipts-15
- https://datatracker.ietf.org/doc/html/draft-xkumakichi-xaip-receipts-03
- https://datatracker.ietf.org/doc/html/draft-helixar-hdp-agentic-delegation-03
- https://datatracker.ietf.org/doc/bofreq-kuhlewind-audit-agent-use-of-delegation-and-interaction-traceability/

## Suggested implementation sequence

1. **Projection contract first.** Separate *sender*, *signer*, *recipient*, *observer*, and *holder*; allow a message to bind typed claim fields rather than only operation sets. Preserve the existing `G/S/X/R` path as a compatibility profile.
2. **Partial, explicit baselines.** For each draft, implement exactly its guaranteed statements and its optional profiles separately. A field not mandated by a draft must not be silently treated as signed evidence, and a non-compliant sender must not be assigned an unearned receipt.
3. **Case adaptation.** Re-evaluate the nine H-classes for whether they are semantically applicable to a draft. Mark non-applicable cases `N/A`, not `fail`. Add cases for signature-valid false claims, omission, truncation, holder-binding, revocation staleness, and external gate compromise.
4. **Independent witness extension.** Introduce service boundary observations as a genuinely separate trust domain with explicit corruption/collusion assumptions. Sending an executor's false receipt directly to P is not independent observation.
5. **Only then score.** Use the same adjudicator *where the evidence vocabulary permits*, record any changed adjudicator assumptions, report outcome per case, and distinguish prevention from adjudication.

## Evidence-to-verdict case template

| Case | World A | World B | Draft evidence reachable by adjudicator | Same evidence? | Valid conclusion | Preconditions |
|---|---|---|---|---|---|---|
| H4/H5 | executor overreach + honest receipt loss | intermediary widening + withheld acknowledgement | **Not evaluated** | **Not evaluated** | **Not evaluated** | Which original signatures and produced copies exist? |
| H6/H7 | downstream cover story | sincere external-effect misattribution | **Not evaluated** | **Not evaluated** | **Not evaluated** | Is there evidence from outside the colluding chain? |
| H8/H9 | upstream false narrowing | real unauthorized subgrant | **Not evaluated** | **Not evaluated** | **Not evaluated** | Does E hold independently verifiable P-origin evidence? |

Do not reuse the existing 8/9 or 6/9 figures as scores for these drafts. These figures belong to *Tallystick's own protocol specifications*.

## Evidence standard for publication

A table entitled “what each draft settles on nine cases” is publishable only when (a) the mapping is revision-pinned, (b) the protocol author's requirements are distinguished from deployment assumptions, (c) held/withheld signed artifacts are derived rather than hand-assigned, (d) expected outcomes are checked under evidence isolation, and (e) `make check` passes in the full repository. External review of at least one mapping is strongly preferred.
