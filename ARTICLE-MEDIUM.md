# The Execution Record Is Not Evidence

### Durable execution can reconstruct what an AI agent did. It cannot, by itself, settle a dispute between the agent and the principal that delegated to it.

---

In May I wrote [*Agent Workflows Are Rediscovering Durable Execution*](https://nittikkin.medium.com/agent-workflows-are-rediscovering-durable-execution-be110661ed8c), and I ended on this:

> The genuinely new work is accountability for non-human, probabilistic actors that can act across
> tools, systems, and organizational boundaries. That is the layer worth fighting for.

I also wrote, about the run record - definition hash, workload identity, idempotency keys, recorded
model outputs, policy decisions, append-only history:

> That is not just a debug log. It is evidence.

I was half right, and the half I got wrong is the half that matters. I spent the following weeks
building an adversarial harness to test that claim properly, and I need to correct it.

**The run record is evidence against failure. It is not, by itself, independently defensible evidence against disagreement.**

More precisely: an executor-maintained run record is *unilateral evidence*. It is excellent for
reconstruction. But when the counterparty disputes the record itself, the question changes from
"what does the log say?" to "why should either side accept this log as authoritative?"

Those are different problems and I had collapsed them. Against a crash, a retry, a partial saga,
the execution history is exactly right - nobody disputes it, they just need to reconstruct what
happened. Against a *dispute*, where one party is self-interested and may also be sincerely wrong,
the same record settles nothing. Because whoever holds it is a party to the argument.

Here is the situation that breaks it.

---

## The dispute the run record cannot settle

You give an agent permission to do three things. It does two. Later you say it did a fourth thing
you never authorised - maybe you misremember, maybe it is convenient to say so now.

The agent is innocent. Can it prove that?

Look at what it has. An append-only history it maintained itself. A definition hash it computed
itself. Recorded model outputs it wrote itself. Every one of those artifacts is produced by the
party under accusation, which makes it precisely the evidence a suspicious counterparty discounts.

The orchestrator's log is not neutral either, if the orchestrator is operated by one side.

This is not a gap in anyone's implementation. It is structural, and I wanted to know how much it
costs. So I measured it.

## Measuring it instead of arguing about it

The harness is deliberately boring. It generates delegation disputes as structured scenarios: what each party actually did, and what each party *claims*. It knows nothing about cryptography. Whether an adjudication scheme catches the discrepancy is the scheme's problem, scored separately.

Then it runs eighteen adjudication schemes against thirty-four adversarial scenario classes - executor misconduct, principal repudiation, sincere mistake, benign failure, abuse of the dispute mechanism itself, adjudicator collusion, and protocol abort.

The architecture has one rule that matters: an adjudication scheme receives a *projection* of the world, never the world. No argument passed to a protocol carries ground truth. This is enforced structurally and verified by mutating every hidden field thousands of times and requiring no verdict to move. The visibility test also includes a deliberately leaking protocol and requires the checker to catch it, so a green result cannot come merely from a vacuous test.

That rule exists because the first version didn't have it, and one of my schemes was quietly reading the answer key. Its results looked excellent. More on that below.

Each of the thirty-four classes has twenty-five deterministic, seeded instances: **850 scenarios total**. So a headline result such as 100/100 means "all twenty-five instances in each of four named classes," not "100 observed incidents in production." This harness measures behaviour over a constructed corpus. It does not estimate prevalence.

Here are the checks behind the claims that follow:

| claim | population | result pinned by the tests |
|---|---|---|
| evidence isolation | all 18 protocols over representative scenarios from all 34 classes | mutate hidden fields and require no verdict change; inject a deliberate leak and require detection |
| assertional principal dispute | M5, M6, M7, M9 × 25 | bearer-log baseline 0/100; bilateral commitment 100/100 |
| non-assertional principal misconduct | M13, M26, M28, M32 × 25 | bearer log 0/100; bilateral commitment 0/100; witness messages 50/100; duty-to-answer 100/100 |
| duty-to-answer trade | five guilty/honest twin pairs × 25 | 125 misses removed and exactly 125 false contradictions introduced |
| conservation boundary | 10 verified twin pairs × 18 protocols | every pair lands on the side predicted from its observable evidence and divergence signature |
| build-gate non-vacuity | the gate itself | a masked pipeline failure must make the gate fail |

## Result one: the default provides no defence against an assertional lie

The baseline I use for a straightforward deployment - bearer token, executor-maintained log - scores **zero out of a hundred** on the four classes where the principal makes an assertion that conflicts with the committed authorization or delivery record.

A scheme where both parties commit to the authorization bilaterally scores a hundred out of a hundred on those same four classes.

That gap is not subtle. But it is also narrower than I first claimed.

## Result two: commitments only help when there is an assertion to contradict

This is where I had to correct myself, and it is the more interesting half.

I originally measured that hundred-out-of-a-hundred over four scenario classes. When I later derived the full set of classes where the principal is dishonest *and the agent is correct*, there were four more - and the bilateral scheme scores **zero** on all four, exactly as the naive default does.

The difference is the kind of lie:

- **An assertional lie** claims something a signature contradicts. "I only granted two operations" when you signed three. Bilateral commitment demolishes this.
- **Non-assertional misconduct** gives the verifier no signed proposition to contradict: a baseless complaint that probes for information, a refusal to produce your own copy of the record, or an abort before acknowledging a delivered result.

Commitments answer the first kind and are silent on the second. Witness-carrying messages reach some of the non-assertional cases, and a *duty to answer* reaches the withholding cases by making refusal itself observable. In this corpus that takes the non-assertional result from 0/100 for bilateral commitment to 50/100 for witness messages and 100/100 for the duty-to-answer scheme.

Which brings us to the thing that cannot be fixed.

## Result three: the duty to answer changes who pays, not how much

Add that duty and the withholding scenarios resolve cleanly. The agent that tampered with its record and then claimed it was unavailable is now contradicted.

So is the agent that genuinely lost its record.

I measured this precisely: five guilty scenario classes resolved, five honest twin classes broken, exactly one for one. **Adding the duty** converts a hundred and twenty-five missed detections into a hundred and twenty-five false contradictions. The abort pair is common to both schemes and is not part of that 125-for-125 exchange.

There is a clean reason. Non-production is a one-bit signal, and both worlds emit it. A mechanism reading only that bit cannot carry two bits of information. So:

> **The duty to speak does not buy resolution. It buys a change of victim.**

Under the permissive scheme, the cost falls on whoever was genuinely wronged, because real misconduct goes unpunished. Under the strict scheme, it falls on the honest party who genuinely lost a record and is now contradicted for it.

Neither is free, and no amount of cryptography decides which is preferable. That is a policy question wearing a technical costume.

## The boundary, stated honestly

Generalising this gives the project's central result. If two underlying worlds produce identical observable evidence, an evidence-determined adjudicator must issue the same verdict in both. The only remaining question is whether one verdict can be correct in both worlds.

Write **D(w)** for the set of parties whose account diverges from the record in world *w*. For two worlds that produce identical evidence:

- If **D is the same in both**, some verdict is true in both, and a mechanism that talks about *the record* rather than *the person* resolves the pair at no cost.
- If **D differs**, no verdict is true in both, and every mechanism must be wrong about one of them.

In plain terms: **twins differing only in *why* a divergence happened are escapable. Twins differing in *whether* one happened are not.**

Mistake versus malice is the first kind - the account contradicts the record either way, and only the intent behind it differs. That is why non-attributive language ("this account contradicts the record") is strictly better than attributive language ("this party is at fault"): it converts an unwinnable question into a winnable one.

Loss versus concealment is the second kind. In the honest world nothing diverged at all. No vocabulary rescues you.

I want to be careful about how much weight this carries. The proof is one line - identical evidence yields one verdict, so the only question is whether one verdict can be correct in both worlds. It is not a deep theorem, and I would be embarrassed to present it as one. What makes it worth having is that it *predicts*: for every ambiguous pair and every mechanism, it says in advance which side of the line the pair falls on, and the test suite recomputes that prediction on every build.

---

## What the fix actually looks like

Concretely, take the run record from that May article and mark up which fields survive a dispute.

```jsonc
{
  "runId": "run-2026-05-14-001",
  "workflowVersion": "1.0.0",
  "definitionHash": "sha256:abc123",     // computed by the executor, held by the executor
  "actor": {
    "workloadId": "spiffe://example.com/prod/agents/release-review"
  },
  "history": [
    { "sequence": 1, "node": "load_pr",       "idempotencyKey": "ik-9f2a" },
    { "sequence": 2, "node": "risk_analysis", "recordedOutputRef": "blob://..." },
    { "sequence": 3, "node": "policy_check",  "decision": "needs_approval" }
  ]
}
```

Every field is real and useful. Not one of them is *bilateral*. Delete the whole structure and
nobody outside can show it ever existed; alter it before disclosure and nobody outside can show it
changed. Under dispute this is telemetry.

The minimal change is small, and it is not a new cryptographic primitive:

```jsonc
{
  "runId": "run-2026-05-14-001",
  "definitionHash": "sha256:abc123",

  // 1. AUTHORIZATION IS COMMITTED BY BOTH SIDES, BEFORE EXECUTION.
  //    The principal signs a commitment to the scope it granted. The executor
  //    signs a receipt for that commitment. Each side now holds the OTHER's
  //    signature over the same root, so neither can later deny the grant and
  //    losing your own copy destroys nothing.
  "authorization": {
    "scopeRoot": "sha256:9c41...",                  // Merkle root over granted operations
    "principalSignature": "...",                    // held by the executor
    "executorReceipt": "..."                        // held by the principal
  },

  // 2. THE EXECUTION RECORD IS COMMITTED THE SAME WAY.
  //    The receipt is what closes the fairness gap: without it the principal
  //    holds nothing about what was actually done.
  "execution": {
    "actionsRoot": "sha256:4b7e...",
    "executorSignature": "...",                     // held by the principal
    "principalAck": "..."                           // held by the executor
  },

  // 3. THE POLICY DECISION IS SIGNED BY ITS ISSUER, NOT BY THE RUNTIME.
  //    This one you may already have: a decision signed by the policy engine
  //    has an independent issuer, which is what makes it different in kind
  //    from the surrounding history.
  "policyDecision": {
    "policyVersion": "release-policy@2026-05-01",
    "decision": "needs_approval",
    "issuerSignature": "..."
  }
}
```

If you're carrying this over A2A specifically, `docs/prior-art/a2a-extension-sketch.md` in the
repository maps these fields onto A2A's own extension mechanism
(`AgentCard.capabilities.extensions` plus namespaced message `metadata`) rather than a bespoke
channel. `src/extensions/a2a_bilateral/` now contains the dependency-free reference library and a
standalone adapter-parity check over the existing corpus. It is still not a new scored protocol:
concrete SDK message parsing remains deployment-specific, and the canonical figures remain those
produced by the existing harness.
Within the repository, the same exchange is a concrete transport for B1 and a future fixture for
B13/B17 receipt availability and the M30-M33 abort/loss cases; `docs/extension-use-map.md` keeps
implemented reuse separate from proposed work.

### Why this is cheaper than it looks

The useful property is not the countersigning. It is that **a commitment can be checked against a
claim without opening it.**

If the principal asserts "I only granted `deploy:staging` and `read:logs`", recompute the Merkle
root from *what it just asserted* and compare to `scopeRoot`. Mismatch means the assertion is false.
The true scope is never disclosed, because the only input to the check is what the claimant
volunteered.

In my measurements that check cost 354 bytes at a 2-operation scope and 360 bytes at 64 operations
- effectively flat - against 237 to 1374 bytes for disclosing the record. It also reaches a case no
query can: an executor that performs an out-of-scope action and simply omits it. You cannot ask
about what you were never told, but you can check what it *did* tell you.

### What it still does not fix

The executor can act and then never send the execution receipt. The principal ends up holding a
commitment to the authorization and nothing about the execution.

In my corpus that class is missed outright by the witness-carrying design, and it is the same
asymmetry optimistic fair exchange was invented to close. If you are building this, that is the leg
to think hardest about - it maps directly onto abort and partial-failure handling, which is
familiar territory from sagas.

---

## Standards you can build this from

None of this requires new cryptography. The parts are standardised, and several are probably in
your stack already.

| need | standard | note |
|---|---|---|
| Non-repudiation framework, origin and delivery | **ISO/IEC 13888** (parts 1-3) | The standards-body version of the 1996-2010 literature. Defines non-repudiation of origin, delivery, submission and transport. Directly on point and rarely cited in agent work. |
| Tamper-evident append-only log with inclusion and consistency proofs | **RFC 6962** (Certificate Transparency), **RFC 9162** (CT 2.0) | Merkle-tree logs with membership proofs. The mechanism above is CT's structure applied to delegation records. |
| Signed timestamps from an independent authority | **RFC 3161** Time-Stamp Protocol | Answers "this existed before that", which ordering disputes need. |
| Detached signatures over structured payloads | **RFC 9052 / 9053** (COSE), or JWS (**RFC 7515**) | COSE if you are size-sensitive, JWS if you are already JOSE-native. |
| Workload identity for the actor | **SPIFFE / SPIRE** | Which running workload made the call, attested and rotated. |
| Externally-issued authorization decisions | **OPA**, **Cedar**, **OpenFGA** | Sign the decision, record the policy version. An unsigned decision inherits the runtime's trust level. |
| Agent-to-agent transport and task lifecycle | **[A2A v1.x](https://github.com/a2aproject/A2A/blob/main/docs/specification.md)** (Linux Foundation) | Defines authentication and authorization responsibilities using standard web mechanisms, while leaving authorization policy agent-defined. It does not define the bilateral delegation evidence considered here. |
| Tool access | **[MCP 2026-07-28 + Tasks](https://modelcontextprotocol.io/extensions/tasks/overview)** | Tasks moved out of the experimental core into the `io.modelcontextprotocol/tasks` extension. It provides durable asynchronous execution state, which helps lifecycle/reconstruction but does not by itself create bilateral adjudication evidence. |
| Audit obligations you may be under anyway | **ISO/IEC 42001**, **EU AI Act**, **SR 11-7** | These require reconstructability and human oversight. Worth checking whether your obligation is "reconstruct" or "adjudicate", because they need different artifacts. |

The gap is not that the primitives are missing. It is that nothing assembles them into a delegation
record both parties hold.

---

## The part that should bother the field

Here is the history.

The property "a correct party can always defend itself against false accusation" is not new. It is present in at least four research lines between 1996 and 2010:

- **Zhou and Gollmann's** non-repudiation protocols
- **Asokan, Shoup and Waidner's** optimistic fair exchange
- **PeerReview** (SOSP 2007), whose accuracy theorem states it almost exactly
- **Rial and Preneel's** optimistic fair priced oblivious transfer

Every one of these is a mature, well-cited line of work with the accused party's defence as a first-class design goal.

**In the specific agentic-identity proposals I originally checked, I found none of those four older lines cited. But a broader claim that current work lacks verifiable delegation evidence is no longer defensible.**

The 2026 landscape is moving quickly. The active IETF **[Delegation Receipt Protocol (DRP)](https://datatracker.ietf.org/doc/draft-nelson-agent-delegation-receipts/)** draft requires a user-signed authorization object to be anchored in an append-only log before execution. The **[Human Delegation Provenance Protocol (HDP)](https://datatracker.ietf.org/doc/draft-helixar-hdp-agentic-delegation/)** draft carries signed human delegation context through a chain of agent hops. And in payments, FIDO's work around **[AP2 and Verifiable Intent](https://fidoalliance.org/building-the-trust-layer-for-agentic-payments-with-ap2-and-verifiable-intent/)** explicitly describes portable cryptographic evidence of user intent and names dispute resolution as a use case. NIST's **[AI Agent Standards Initiative](https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure)** is another sign that secure agent identity and delegation are now active standards work.

That changes the honest claim. The interesting gap is no longer *"nobody is building verifiable authorization."* They are. The question this project tests is narrower: **what can those artifacts actually settle when authorization, execution, withholding, abort, and sincere mistake become competing accounts in a dispute?** DRP is very close to the assertional half of that problem; HDP is strong on provenance; AP2/Verifiable Intent is deliberately domain-specific evidence of intent. I have not found, in the sources reviewed here, the full adversarial adjudication model used by this harness: bilateral authorization and execution evidence evaluated against repudiation, non-production, abort, and honest error as separate worlds.

That is also why the old fair-exchange and non-repudiation literature still matters. Current work is rediscovering adjacent evidence mechanisms; the older literature supplies a mature vocabulary for fairness, counterparty-held evidence, and the accused party's ability to defend itself.

### To be clear about what people *are* working on

It would be wrong to say nobody is looking at agent accountability. As of mid-2026 there is work on protocol gaps, verifiable delegation and intent, and secure agent standards. Systematic analyses still find audit and replay absent or only partially supported across several interoperability protocols, but that is now only one part of the landscape.

But that work asks a different question from this one, and the difference is the whole point.

**Audit asks: can we reconstruct what happened?** That is a question about a record, and it assumes we agree on the record once we have it.

**Adjudication asks: whose account do we believe, when both parties are self-interested and one of them may be sincerely wrong?** That is a question about a *disagreement*, and no amount of logging settles it if the log is kept by a party to the dispute.

Here is the concrete version. A2A's official [extension catalog](https://github.com/a2aproject/A2A/blob/main/docs/topics/extensions.md) includes a Traceability extension, and its [enterprise guidance](https://github.com/a2aproject/A2A/blob/main/docs/topics/enterprise-ready.md) recommends distributed tracing with trace IDs, span IDs, task IDs and correlation IDs. That is genuinely useful observability. But the traceability machinery does not, by itself, create a mutually committed or independently held record that survives one party disputing the trace.

A2A v1.x does specify authentication and authorization responsibilities: servers authenticate requests according to the schemes they advertise, and they must authorize protocol operations. The authorization model itself remains agent-defined and implementation-specific. My point is therefore not that A2A lacks security. It is narrower: **authentication and authorization do not automatically create counterparty-held evidence for adjudicating a later delegation dispute.**

That is what the zero-out-of-a-hundred number above is measuring.

This is the finding most likely to change what someone builds this quarter, and it required no harness at all. Just reading.

---

## The correction that caught the checker

A note on method, because I think it generalises past this project.

During the hardening pass, six documented claims turned out to be false. Not typos - stated claims I had reasoned my way to and believed. They all had the same shape: **a universal statement inferred from the subset in front of me.** Two scenario classes declared indistinguishable that were not. A behaviour I modelled for one party while believing I had modelled it for both. A scenario class I described as resisting *every* mechanism when I had only checked one family. A measurement whose denominator quietly excluded the cases where my preferred mechanism performed no better than the baseline it was supposed to beat.

Then, during the final publication review, the same failure happened again. The abort class M32 had been added after the non-assertional F01 population was derived. The corpus now contained four relevant classes; the declaration still named three. The declaration auditor correctly detected the disagreement.

And `make check` still went green.

The reason was painfully ordinary: the audit command was piped through `tail`, and the shell returned `tail`'s successful exit status instead of the validator's failure. The checker was correct; the composition of the checker into the build was not.

I fixed both sides. The principal-dishonesty population is now pinned by a regression test derived from corpus ground truth, M32 is included in the non-assertional set, the build runs with pipeline failure propagation enabled, and the gate has a non-vacuity test that deliberately fails the left side of a pipeline and requires the build to notice. The suite now contains 158 unit/property/regression tests, plus the structural validation stages around them.

Not one of these corrections was caught by re-reading. They were caught by deriving structure from the system and diffing it against what the documentation or build claimed. So the rule I would now apply anywhere:

> Anything hand-maintained should be recomputed against the system it describes, and the recomputation should fail the build when they disagree.

And a corollary with considerably more bite than I intended when I first wrote it:

> "Checked" always needs "in what dimension, and does failure actually propagate?" attached.

---

## What this doesn't tell you

The limitation that matters most: **nothing here measures how often principals actually misremember.** The mistake scenarios are constructed. They are plausible and they match ordinary experience, but the *rate* is the parameter that decides whether any of this matters in deployment, and it is unmeasured. It would need real traces from real deployed agents.

I mention it prominently because burying it would commit exactly the overclaim this project exists to criticise.

Also: the disclosure costs are comparable between schemes but are not a cost model for anything real. Whether thirty-four scenario classes span the space is unproven. And every audit here is my own, including the audits of the audits. The publication review finding another stale declaration *and* a masked gate failure is evidence that this caveat deserves to remain prominent.

---

## If you are building this

What I would take away:

1. **Ask whether your agent can defend itself**, not only whether you can prove it was authorised. If the agent's own log is the only evidence, the answer is no - and this is the question I did not ask in May.
2. **Prefer language that talks about the record over language that talks about the person.** "These accounts contradict the record" is provable. "This party is at fault" often isn't, and the difference shows up as false accusations of parties who simply misremembered.
3. **Sort your records into two piles: reconstruct, and adjudicate.** Correlation IDs, traces and append-only history answer *what happened*. They do not answer *whose account do we believe*. Anything in the second pile needs a second holder, and the test is simple: if this party deleted its copy, could anyone outside show the record existed?
4. **Sign policy decisions at the issuer.** This is the cheapest real win available. A decision signed by the policy engine has an independent issuer; the same decision written into the runtime's own history does not, and inherits the runtime's trust level.
5. **Read the older papers *and* the 2026 drafts.** The field is moving fast enough that both failures are possible at once: rediscovering a thirty-year-old fairness result and missing a three-month-old delegation protocol.

The harness, the corpus, and the full research record - including every correction - are open. The most useful thing anyone could do with it is try to break the visibility invariant and tell me it leaks.

---

*Tallystick is an independent research project. The code, corpus, canonical results, and complete correction record are included with the accompanying repository.*
