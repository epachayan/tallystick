# Articles

Public-facing write-ups. The general-audience draft is kept **in the repository** so it is covered
by the same staleness checks as everything else. The technical Medium article, "The Execution
Record Is Not Evidence", is maintained outside the repository and is not part of a release; the
history below is kept as the record of its checks. An article published from a stale copy is the
most expensive kind of drift: unlike a findings note, it cannot be quietly corrected after the fact,
so its figures must be re-verified by hand against `results/canonical.txt` before it goes out.

| file | audience | status |
|---|---|---|
| technical article (outside the repository) | practitioners building agent infrastructure | **canonical technical/Medium draft.** Written as a sequel to the May 2026 durable-execution piece and opens by correcting it. |
| [`02-general-audience.md`](02-general-audience.md) | no technical background assumed | draft, unpublished |

## Before publishing either

1. **Add the verified public repository URL at publication time.** The packaged drafts intentionally
   omit a hard-coded public URL. The private repository exists at `github.com/epachayan/tallystick`;
   add the link only after it resolves while signed out.
2. **Check every number against `results/canonical.txt`.** The articles quote figures in prose,
   where the staleness checker cannot parse them. The quoted claims are listed below so they can be
   re-verified by hand.
3. **Supersede the phase-1 drafts.** An earlier pair of articles was written before the hardening
   phase. They state the conservation property unbounded, F01 unscoped, and the M22 claim that was
   later refuted. If either is already live it needs correcting or withdrawing.

## Claims quoted in prose (verify by hand)

| claim | source |
|---|---|
| bearer-token baseline scores 0 of 100 on assertional principal dishonesty | `[F01]` in canonical.txt |
| bilateral commitment scores 100 of 100 on the same | `[F01]` |
| bilateral commitment scores 0/100 on the four non-assertional classes | `[F01]`, non-assertional block |
| duty to answer: five classes resolved, five honest twins broken, one for one | `findings/10`, `findings/11` |
| 125 misses become 125 false contradictions | `tests/test_b17.py` |
| four pre-2011 self-defence/fair-exchange lines; absence claim scoped to proposals originally reviewed | `RESEARCH.md` §7 + `../prior-art/2026-protocol-landscape.md` |
| six hardening declaration defects, plus RC-H15 publication-gate drift | `RESEARCH.md` §9a + `../test-evidence-map.md` |

## Patched 12 August 2026

The technical article had two correctness problems during drafting, both now fixed:

1. **An unqualified universal claim** - "none of them is cited by the 2024-2026 agentic-identity
   literature." That is the exact shape of statement that produced six defects in this project.
   Now scoped to the proposals actually read, dated, and with an explicit invitation to supply
   counterexamples.
2. **It implied nobody is working on agent accountability.** No longer true as of mid-2026, and
   easy to falsify. The article now states the audit-versus-adjudication distinction directly and
   names A2A's Traceability extension as the concrete example of telemetry standing in for
   evidence.

Background for both: [`../prior-art/2026-protocol-landscape.md`](../prior-art/2026-protocol-landscape.md).

## The reframe (14 August 2026)

The technical article was retitled and reopened as **"The Execution Record Is Not Evidence"**, a
self-correction of the May 2026 article
[*Agent Workflows Are Rediscovering Durable Execution*](https://nittikkin.medium.com/agent-workflows-are-rediscovering-durable-execution-be110661ed8c),
which asserted that the run record "is not just a debug log, it is evidence."

That is true against **failure** and false against **disagreement**, and the distinction is the
whole finding. The reframe does three things the previous opening did not: it earns the F01 result
instead of asserting it, it reaches an audience already thinking about SPIFFE, OPA and saga
compensation, and self-correction is the register this project is strongest in.

Added with the reframe: an annotated run record showing which fields survive a dispute and which
do not, a minimal bilateral version, and a table of standards the design can be assembled from
(ISO/IEC 13888, RFC 6962/9162, RFC 3161, COSE/JWS, SPIFFE, A2A, MCP).

## The one thing not to soften

Both drafts state that the prevalence of principal misremembering is **unmeasured**, and both do so
prominently rather than in a closing caveat. That placement is deliberate. It is the parameter that
decides whether any of this matters in deployment, and burying it would commit exactly the
overclaim this project exists to criticise.


## Final publication additions (15 August 2026)

The final technical article also includes a compact evidence table mapping each headline claim to
its population and the regression that pins it. Detailed mappings live in
[`../test-evidence-map.md`](../test-evidence-map.md). The article was updated for A2A v1.x authentication/authorization semantics. On 15 August it
was refreshed again for MCP 2026-07-28 Tasks-as-extension, DRP, HDP, AP2/Verifiable Intent and
NIST's agent-standards initiative; the novelty claim is now explicitly about adversarial
adjudication rather than the absence of verifiable delegation evidence.
The repository-specific implementation boundary is maintained in
[`../extension-use-map.md`](../extension-use-map.md): B1 carriage is implemented, while B13/B17 and
abort/loss fixtures remain proposed reuse rather than article evidence or additional scores.
