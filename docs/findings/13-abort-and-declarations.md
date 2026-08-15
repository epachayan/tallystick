# 13 — Abort, and the last four declarations

**Date:** 11 August 2026 · **Closes:** RC-H7, RC-H12
**Corpus:** 34 classes / 850 scenarios · **Gate:** 158 tests + gate non-vacuity

Two items, done together because the first changed what the second had to check.

---

## Part 1 — RC-H12: the four remaining declarations

Four hand-maintained declarations had never been derived and diffed. The base
rate going in was four defects in four audits. Two of these four were wrong.

| declaration | verdict |
|---|---|
| `mutation_family` | agrees |
| `ENTITLEMENTS` | agrees |
| `PRINCIPAL_LIAR` | **wrong — and it was flattering F01** |
| `src/commitments.py` BINDING/RESIDUAL | **wrong criterion** |

### PRINCIPAL_LIAR was measuring F01 on a favourable subset

The declaration held `{M5, M6, M7, M9}` and was used as the F01 denominator. The
corpus contains six more classes with a dishonest principal, and in four of
them the executor is correct — so "can a correct executor defend itself?" is a
fair question about them too.

It cannot:

```
  assertional (M5 M6 M7 M9):
    B0_bearer_executor_log      0/100 correct blame
    B1_bilateral_commitment     100/100 correct blame

  non-assertional (M13 M26 M28 M32):
    B0_bearer_executor_log      0/100 handled
    B1_bilateral_commitment     0/100 handled
    B13_witness_messages        50/100 handled
    B17_duty_to_answer          100/100 handled
```

**B1 scores zero on the non-assertional classes, exactly as B0 does.** The
excluded classes were the ones where the project's headline mechanism performs
no better than the deployed default it was introduced to beat.

The claim is not withdrawn; it is scoped, and the scope turns out to be the
interesting part:

> Bilateral commitment lets a correct executor defend itself against an
> **assertional** lie — the principal asserts something a signature contradicts.
> It does nothing against a lie that makes no assertion: a baseless complaint
> (M13), a withheld record (M26, M28), or an abort before acknowledging delivery
> (M32). Witness messages reach two of the four; the duty-to-answer scheme handles all four.

That is a better result than the unscoped version, because it says *which
mechanism for which lie* rather than "commitments help".

### commitments.py had the right residual for the wrong reason

The module declared M19, M20 and M22 residual — "no party-made commitment can
bind these" — with a per-class criterion. Measured per class, that is false:
`C_retain` ("produce your record on demand") is already in its own vocabulary,
and B17 implements exactly it, and B17 reaches M19 and M20.

But B17 pays for M19 with M10 and for M20 with M21. So the criterion needs to be
pairwise:

> **BINDABLE** — some commitment forces the act into contradiction *without
> contradicting its evidentially identical honest twin*.

Under the pairwise criterion the residual entries are correct again, and for a
sharper reason. And the two analyses collapse into one:

**A class is bindable exactly when its twin pair is ESCAPABLE — when
D(guilty) = D(honest).** The minimal-commitment-set analysis and the
conservation boundary of finding 12 are the same result in two vocabularies.
That was not visible while bindability was assessed one class at a time.

---

## Part 2 — RC-H7: abort

Every class in the corpus assumed the message chain completes. B13's witness
chain has a fairness asymmetry after step 2 — the executor holds evidence of
origin while the principal holds nothing about the execution — and nothing could
see it.

Four classes, two twin pairs:

| class | |
|---|---|
| M30 | executor acts, then aborts before sending the execution receipt |
| M31 | the execution receipt is lost in transit; the executor acted correctly |
| M32 | principal aborts before acknowledging a delivered result |
| M33 | the delivery acknowledgement is lost in transit |

### An abort hides the commitment, not the contents

M30/M31 turned out to be a twin pair **only under commitment-only disclosure**.
Under full disclosure the overreach is plainly visible in the execution record:
aborting buys the executor nothing against an adjudicator who can read it.

That is a distinction worth having and it is recorded as a distinct twin status
rather than forced into the existing one. It also says something practical:
**abort is an attack on commitment acquisition, not on evidence.** A mechanism
that can compel disclosure is unaffected by it; a mechanism built on
counterparty-held commitments is not.

### The predicted gap is real

**B13 misses M30 outright.** The principal never receives the execution receipt,
so it holds no commitment over the execution, so there is nothing to recompute
an assertion against. This is precisely the asymmetry flagged when B13 was
built, now measured rather than suspected.

On the other leg, B13 and B17 both catch M32 — and both false-contradict M33 for
it. Before the abort classes existed, B13 made **no false contradiction
anywhere**. It now makes exactly 25, all on M33. The conservation, arriving
again in a place that had looked clean.

### What this does to the headline figures

B13 and B17 both land at 26/34 with a 0% false-attribution rate. The four new
classes did not lower their standing relative to other mechanisms — B10 also
sits at 26/34 — but they did convert B13's "no false contradictions" into "no
false contradictions except on the abort leg", which is a materially weaker and
more accurate statement.

**RC-H7 is closed and the caveat it carried is resolved:** the earlier figures
were upper bounds, and the abort classes show by how much and where.

---

## Standing claims

**T8 — holds, in a fourth denomination.** M30/M31 and M32/M33 are both binding
pairs and the boundary predicts them without modification. Nothing about aborts
required a new theory.

**F01 — scoped, not withdrawn.** See above. The scoping is the finding.

**T10 — restated a third time.** The residual is pairwise, not per class, and it
is the same set the conservation boundary identifies.

**Fair exchange is now motivated by a measurement rather than by the
literature.** M30 is the class it exists to close, and B13's failure on it is
the specific gap. That is a better starting point than "the prior art says we
should have one".

---

## What remains

- **RC-H13** B11 is scored per scenario; whether repetition escapes the
  conservation boundary is still the most interesting untested question.
- **A fair-exchange baseline**, now with a concrete target: M30.
- **RC-H2** the authoritative M-class list, now against 34 classes.
- **N1** misremembering prevalence, still outside the harness and still the
  largest gap in any deployment claim.


## Publication review correction — RC-H15

This finding originally scoped the non-assertional population to M13/M26/M28 even though the same
change set added M32. The declaration auditor later detected the mismatch; a shell pipeline in the
Makefile masked its failing exit status. The final repository fixes the population, adds dedicated
headline-claim regressions, enables `pipefail`, and tests the gate's failure propagation directly.
