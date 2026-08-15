# The 2026 agent protocol landscape, and where this work sits in it

**Updated:** 15 August 2026 · **Sources checked:** primary specifications/drafts plus cited gap analyses · **Status:** scoped review, not systematic

This file exists to stop a dangerous sentence from becoming a project invariant. Earlier versions of the research record said the accused-party defence found in 1996-2010 work was absent from the current agentic literature. That was true only for the identity/delegation-token proposals actually read at the time. By mid-2026, adjacent work on signed delegation receipts, human-delegation provenance, verifiable intent, and agent standards is close enough that the boundary must be stated much more carefully.

## What exists now

### A2A

A2A v1.x is agent-to-agent transport and task lifecycle. It defines authentication and authorization responsibilities using standard web mechanisms: clients discover advertised security schemes, servers authenticate requests, and operations must be authorized. The authorization policy/model remains agent-defined and implementation-specific. Its extension catalog includes Traceability and related enterprise observability guidance. Those mechanisms improve reconstruction; they do not by themselves define the bilateral counterparty-held authorization-and-execution record tested here.

Primary sources: [A2A specification](https://github.com/a2aproject/A2A/blob/main/docs/specification.md), [extensions](https://github.com/a2aproject/A2A/blob/main/docs/topics/extensions.md).

### MCP

MCP is tool-centric. In the 2026-07-28 revision, Tasks moved from the 2025-11-25 experimental core into the `io.modelcontextprotocol/tasks` extension. The extension provides a durable task handle and polling/update/cancel lifecycle for long-running tool execution. That is directly useful for execution lifecycle and reconstruction. It is not, by itself, a mutually held adjudication record.

Primary sources: [2026-07-28 release](https://blog.modelcontextprotocol.io/posts/2026-07-28/), [Tasks extension](https://modelcontextprotocol.io/extensions/tasks/overview).

### Delegation Receipt Protocol (DRP)

The active individual IETF Internet-Draft `draft-nelson-agent-delegation-receipts` is the closest current work to the assertional half of this project. Before execution, the user signs an Authorization Object containing scope and boundaries; the receipt is anchored to a tamper-evident append-only log before the agent receives control. That directly attacks operator-controlled-log ambiguity and makes authorization independently verifiable. The unversioned draft name is intentional: consult the linked IETF page for the current revision.

What DRP does **not** automatically settle is the full dispute model here: what execution occurred, what each side later produces or withholds, protocol abort, and honest mistake versus concealment. In Tallystick terms, DRP is highly relevant prior art for authorization commitment and assertional repudiation, not a substitute for the evidence-projection/twin analysis.

Primary source: [Delegation Receipt Protocol](https://datatracker.ietf.org/doc/draft-nelson-agent-delegation-receipts/) (work in progress; individual Internet-Draft, not an IETF standard).

### Human Delegation Provenance Protocol (HDP)

The active individual Internet-Draft `draft-helixar-hdp-agentic-delegation` defines a signed human-delegation token and an append-only chain of signed agent hops, verifiable offline from the issuer's public key and session identifier. It is strong prior art for provenance across multi-agent delegation. The unversioned draft name is intentional: consult the linked IETF page for the current revision.

Its primary question is provenance: who authorized what scope, and through which delegation chain? Tallystick's question is adjudication under disagreement: when parties present competing accounts, which worlds remain distinguishable from the evidence actually available?

Primary source: [HDP](https://datatracker.ietf.org/doc/draft-helixar-hdp-agentic-delegation/) (work in progress; individual Internet-Draft).

### AP2 and Verifiable Intent

FIDO Alliance work around Google's AP2 and Mastercard/Google Verifiable Intent is a domain-specific counterexample to any broad claim that current agent systems lack portable evidence of user intent. AP2 uses signed mandates to represent user constraints and transaction authorization; Verifiable Intent is explicitly framed as an evidence layer that turns authorization into portable cryptographically verifiable evidence. FIDO also names dispute resolution as a use case.

That work is focused on agentic commerce and payment authorization. It materially narrows the novelty claim here, while leaving the broader adversarial question open: whether authorization evidence plus execution evidence is sufficient under withholding, abort, and sincere mistake.

Primary sources: [FIDO AP2 + Verifiable Intent](https://fidoalliance.org/building-the-trust-layer-for-agentic-payments-with-ap2-and-verifiable-intent/), [FIDO agentic standards announcement](https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/).

### NIST AI Agent Standards Initiative

NIST launched the AI Agent Standards Initiative in February 2026 to advance secure and interoperable agent systems. It is not a protocol that subsumes this harness; it is evidence that agent identity, authorization, interoperability and security are now an explicit standards problem rather than a neglected edge case.

Primary source: [NIST announcement](https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure).

### Other protocol/gap-analysis work

ACP (IBM Research) brings negotiation semantics with FIPA-ACL heritage. ANP uses DID-based routing. ERC-8004 uses on-chain identity, reputation and validation registries. Kang and Diponegoro (arXiv 2606.31498, June 2026) assess several agent protocols against a governance taxonomy and report audit/replay absent or partial across the set they examine. Related taxonomies include Hu and Rong (arXiv 2511.03434) and Ruan (arXiv 2604.11337).

## Where this work is different

The useful distinction is now narrower than "the field forgot accountability." It did not.

| | asks | typical artifact/assumption |
|---|---|---|
| **Authorization / intent evidence** | what did the principal authorize? | signed receipt, mandate, provenance token |
| **Audit / observability** | can we reconstruct what happened? | trace, log, task history |
| **Delegation provenance** | through whom did authority flow? | signed delegation chain |
| **This work** | which account survives a dispute? | parties are self-interested, may dispute the record itself, and may be sincerely wrong |

Three consequences remain distinctive in this harness:

1. **Evidence is projected, not omniscient.** Every protocol receives only the artifacts its trust assumptions entitle it to see; hidden ground truth is structurally unavailable.
2. **Sincere error is first-class.** A principal who honestly misremembers and one who lies can be evidential twins. That matters because an attributive verdict can punish the honest twin even when cryptographic verification is perfect.
3. **Indistinguishable worlds produce a checkable boundary.** When identical evidence corresponds to worlds that require different correct verdicts, no evidence-determined mechanism can resolve both. When the worlds differ only in intent behind the same observable divergence, non-attributive language can escape the pair.

The contribution should therefore be described as a **measurement model and adversarial test framework for delegation adjudication**, plus a boundary over evidence projections. It should not be described as inventing signed delegation, tamper-evident logs, non-repudiation, or verifiable intent.

## What would strengthen the next version

The most useful extensions are no longer "invent an authorization receipt." Current work already occupies that space. Better next steps are:

1. instantiate a DRP-like authorization receipt as a Tallystick protocol and map exactly which M-classes it resolves;
   [`a2a-extension-sketch.md`](a2a-extension-sketch.md) and the linked reference library implement
   the A2A transport and live-input projection for bilateral commitment, but deliberately stop short
   of registering a new scored protocol; the repository-local B1/B13/B17 and abort/loss reuse plan
   is explicit in the [extension use map](../extension-use-map.md);
2. model an HDP-style multi-hop provenance chain and test where provenance helps or merely relocates trust;
3. add a payment-flavoured AP2/Verifiable-Intent family to test domain-specific intent evidence against withholding and abort;
4. seek an external implementation or red-team review of the evidence-projection invariant.

## Scope note

This is **not a systematic survey**. It is a dated positioning review using sources checked through 15 August 2026. DRP and HDP are individual Internet-Drafts and therefore works in progress, not IETF-endorsed standards. AP2/Verifiable Intent are active FIDO workstreams. Claims about what a literature does *not* contain are exactly the shape of statement that produced multiple defects in this project, so any negative claim here is intentionally scoped to the sources reviewed.
