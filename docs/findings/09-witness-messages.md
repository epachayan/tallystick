# 09 — Witness-carrying messages (B13), and what they cost the selective-disclosure line

> **HISTORICAL FINDING.** This was the state before abort/loss classes M30–M33 were added.
> The abort caveat below was subsequently tested and closed by
> [`13-abort-and-declarations.md`](13-abort-and-declarations.md). Current figures and standing
> claims live in [`../what-is-established.md`](../what-is-established.md).

**Date:** 11 August 2026
**Baseline:** `B13_witness_messages`, `src/protocols/baselines.py`
**Gate:** decision gate C in the findings plan — "if witness-carrying messages
solve the problem cleanly, narrow or retire the selective-disclosure line"

---

## The protocol

```
P -> E   authorization, authorization commitment, P's signature
E -> P   receipt, authorization commitment, E's signature
E executes
E -> P   execution receipt, authorization + execution commitment, E's signature
```

Two consequences follow, and the second was not anticipated.

**1. Each party holds the counterparty's signature over the same commitments.**
Losing your own log destroys nothing, because the other side can still produce
the artifact. "I lost my record" stops voiding a commitment, though it still
withholds the contents.

**2. A commitment can be tested against an assertion without opening it.**
If a party asserts a scope, recompute the root from what it asserted and compare
to the committed root. A mismatch contradicts the assertion, and the true set is
never disclosed — the only input to the check is what the party volunteered.

The second is the load-bearing one, and it exposes a mistaken premise that ran
through the whole project. Every baseline before B13 compared an assertion
against the **true** set, so commitment-only adjudication looked semantically
blind: withhold the contents and no scope dispute can be settled. That is wrong.
Commitment-only adjudication is blind to facts **nobody asserted**. Assertions
check themselves, at zero disclosure, because the claimant supplies the input.

## Result

| | full-class | false attribution | disclosure at scope=64 |
|---|---|---|---|
| B3 bilateral, full disclosure | 18/- | 17% | 1374 B |
| B10 composed, full disclosure | 23/- | 0% | 1374 B |
| B7 verifiable, query-based | 20/- | 13% | 365 B |
| **B13 witness-carrying** | **24/-** | **0%** | **360 B** |
| B16c custodial attestor | 25/- | 0% | 486 B |

> Figures restated against the 30-class corpus. `results/canonical.txt` is
> authoritative; `make check` fails if this table drifts from it.

B13 beats every mechanism except the custodial attestor, which only wins by
assuming a third party holds the contents — a custodian, not an attestor, and
declared as an entitlement for exactly that reason.

Disclosure is flat in record size: 354 B at scope 2, 360 B at scope 64, against
237 → 1374 B for full disclosure. There is one query, and it is bounded by the
complaint rather than by the record.

Accuracy is constant across all six scope sizes tested.

## What B13 reaches that queries cannot

**M1, concealed overreach.** The executor performs an out-of-scope action and
omits it from its account. A dispute-driven protocol cannot reach this: the
complainant can only name what the counterparty admitted to, and it was never
told. Recomputing the root from what the executor **did** assert catches it
anyway, without anyone naming the concealed action.

This is the general shape. Query-based selective disclosure is limited by what
the complainant can name. Root recomputation is limited by what the respondent
chose to say. Those are different limits, and the second is the more useful one,
because a liar has to say something.

## The residual

B13 fails exactly six classes: **M19, M20, M22, M24, M26, M28** (the last
two are the principal-side mirrors added later; see finding 11). In every one the
executor asserts nothing about its record and withholds the contents.
`test_b13_residual_is_exactly_the_withheld_record_classes` pins this.

The characterisation is clean:

> Recomputation needs an assertion to check. A party that says nothing cannot
> contradict itself.

So the refuge is no longer "I lost my record" — the counterparty holds the
commitment, so the record's existence and identity survive. The refuge is
**silence**. That is a narrower and more precise residual than T10's, and it
suggests the next question is not what else can be committed, but what obliges
a party to speak.

## Gate C: the selective-disclosure line should narrow

Decision gate C asked whether witness-carrying messages undermine the
selective-disclosure design space. They do, on two counts.

**Accuracy.** B13 reaches 24/- where the entire query-based family (B4–B7,
B6c, B7r) reaches 18–20/-, at comparable or lower disclosure.

**Robustness.** Pad the commitments to hide cardinality — the privacy fix
F-H2 says you may want — and the query-based family loses two classes each,
while B13 loses none:

```
  B4_scope_predicates            18/- -> 16/-   -2
  B5_dispute_driven              18/- -> 16/-   -2
  B6_accountable_queries         19/- -> 17/-   -2
  B7_verifiable_adjudication     20/- -> 18/-   -2
  B6c_under_collusion            19/- -> 17/-   -2
  B7r_under_revocation           20/- -> 18/-   -2
  B13_witness_messages           24/- -> 24/-   +0
```

The query-based results were partly resting on the cardinality a plain
commitment leaks. Fix the leak and they degrade; B13 does not, because its
input is the respondent's own assertion rather than the record's size.
Reproduced by `[F10]` in `results/canonical.txt`.

**Recommendation:** retain B4–B7 as the recorded negative result — exhaustive
and dispute-bounded querying over commitments, and what each costs — and stop
developing the line. The remaining open question in selective disclosure is
narrower than it looked: not "how few queries settle a dispute", but "what
can be settled with no query at all".

## Bearing on the standing claims

**T8, conservation of ambiguity — not falsified, and now sharper.** B13
resolves more at lower cost, but the ambiguity does not vanish: it concentrates
into the four silence classes. Nothing was gained that was not paid for
somewhere; the payment moved from disclosure to a requirement that the accused
party speak.

**T10, commitment residual — needs narrowing twice over.** F-H1 already showed
M19 and M20 are partly reachable through committed cardinality. B13 shows the
residual is not about what commitments can bind but about what assertions exist
to check. Suggested wording:

> Under the commitment families modelled, an act remains unattributable when the
> party performing it makes no assertion the commitment can contradict. Silence,
> not loss, is the residual.

**T4, concealment criterion — supported.** B13's reach is exactly the set of
acts requiring a false assertion. The four it misses require only withholding.
That is T4's boundary, arrived at from a different direction.

**T12, level invariance — untested here.** B13 introduces no new trusted party,
so it says nothing about relocation. Fair exchange is the test for that.

## Historical caveat: the abort gap was untestable on this corpus

The message chain has an obvious fairness asymmetry. After step 2 the executor
holds evidence of origin while the principal holds nothing about the execution;
an executor that acts and never sends the execution receipt leaves the principal
without a commitment to point at.

At the time of this finding, the corpus had no abort, message-loss, delay or replay classes, so B13
was evaluated in a world where the chain always completed. Its 24/- was therefore an **upper bound**
for that corpus version, and the classes it would lose under one-sided abort were unknown.

That gap motivated the later abort work. Finding 13 added M30–M33 and measured the prediction:
B13 misses M30 outright, while the M32/M33 acknowledgement leg forms a binding pair. Delay, replay,
retransmission, and a faithful fair-exchange baseline remain outside the harness.
