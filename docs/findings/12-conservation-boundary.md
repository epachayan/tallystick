# 12 — The conservation boundary

**Date:** 11 August 2026
**Module:** `src/validation/conservation.py` · **Tests:** `tests/test_conservation.py`
**Corrects:** finding 10's claim that M22 resists every mechanism
**Status of T8:** no longer a conjecture supported by examples. A boundary with a proof and a check.

---

## The result

T8 said the cost of ambiguity can only be denominated, never eliminated. It was
argued from three separate observations — disclosure bytes, padding overhead,
and B17's exchange — each showing a cost move rather than vanish. That is
suggestive, and suggestive was the honest label for it.

It is now sharper, and in one respect the earlier claim was **too strong**.
Conservation is not universal. It has an exact boundary, and the boundary is
derivable rather than measured.

Write **D(w)** for the set of parties whose account diverges from the record in
world *w*. For an evidential twin pair (guilty, honest):

| | condition | consequence |
|---|---|---|
| **ESCAPABLE** | D(guilty) = D(honest) | some verdict is true in both worlds |
| **BINDS** | D(guilty) ≠ D(honest) | no verdict is true in both |

In plainer terms:

> Twins differing only in **why** a divergence happened are escapable.
> Twins differing in **whether** one happened are not.

## Why it holds

Not empirical. An evidential twin pair projects to **one** `EvidenceView`. Any
evidence-determined mechanism is a function of that view, so it returns **one**
verdict for both worlds. Whether that single verdict can be correct in both is
therefore a question about the scorer, not about the mechanism.

A non-attributive verdict asserts *these parties' accounts contradict the
record*. Its truth value is fixed entirely by D. So if both worlds share a D,
one such verdict is true in both and a mechanism using that vocabulary handles
the pair. If they differ — and in every binding pair here the honest world has
D empty, because nothing diverged at all — no assertion about D holds in both,
and any mechanism must be wrong about one of them.

## The check

The corpus does not confirm the rule; it checks that the harness obeys it. A
binding pair solved by an unentitled mechanism would mean something reads
outside the view and the visibility invariant missed it.

```
  pair        D(guilty)   D(honest)   verdict      solved both by
  M6/M15      {P}         {P}         escapable    8 protocols
  M7/M17      {P}         {P}         escapable    8 protocols
  M19/M10     {E}         {}          binds        0
  M20/M21     {E}         {}          binds        0
  M22/M23     {E}         {}          binds        0
  M24/M25     {E}         {}          binds        0
  M26/M27     {P}         {}          binds        0
  M28/M29     {P}         {}          binds        0
```

Eight pairs, eighteen protocols, and the boundary predicts every cell. `make
check` recomputes it.

## What this explains that was previously just observed

**Why the non-attributive vocabulary works — and exactly how far.** Findings 03
and 08 established that it prevents over-attribution on mistake-vs-malice twins.
The reason is now precise: those twins share a D, so "your account contradicts
the record" is true in both worlds. It was never a general escape from
ambiguity. It is an exact escape from one of the two kinds, and it buys
literally nothing on the other — B10 on M19/M10 issues the same verdict as B13
and scores `missed` / `correct_abstain` exactly as the boundary requires.

**Why B17's exchange was exactly one-for-one.** All five pairs it traded across
are binding pairs. There was no possibility of a better outcome, and none of the
five could have gone differently. Finding 10 reported the exchange as a
discovery; it is a consequence.

**Why the escapable pairs never showed up in any conservation count.** They
were, correctly, never counted as costs. The conservation observations were
implicitly restricted to binding pairs all along, without that restriction being
stated.

## The correction

Finding 10 claimed M22 "has resisted every mechanism in the set" (corrected here, findings/12) and called it
"the hardest single class in the corpus". **That was wrong.** It was measured
across the commitment-only family only. The full-disclosure protocols — B1, B3,
B9, B10, B11, B15, B16c, B16d — all solve M22, and all fail M23 for it.

Recomputing across all eighteen: **no class in the corpus is unreachable by
every mechanism.** M22 is an ordinary binding twin pair. Every protocol solves
exactly one of M22/M23, which partitions the protocol set 8/10 — the
conservation visible per mechanism rather than in aggregate.

The error is the same shape as F-H3 and RC-H9: a claim about *all* mechanisms
inferred from the subset in front of me. `make check` now recomputes it instead
of trusting the prose.

## Standing claims, restated

**T8 — upgraded and bounded.** No longer "the cost of ambiguity can only be
denominated". The accurate statement:

> Where two worlds project to identical evidence **and differ in whether any
> account diverges from the record**, no evidence-determined mechanism resolves
> both. The cost can be denominated — as false accusation, missed detection,
> disclosure, or padding — but not removed. Where the worlds differ only in the
> *intent* behind a divergence both exhibit, a non-attributive vocabulary
> resolves both at no cost.

The second sentence is new, and it is the part that makes T8 falsifiable rather
than tautological: it predicts *where* a mechanism can win, and that prediction
is checkable.

**T4 — subsumed.** The concealment criterion said malice is separable when it
requires a concealing act. That is the D-condition in different words: a
concealing act is what creates a divergence the honest twin does not have.

**T6 — bounded.** Non-attributive dominance holds on escapable pairs and is
neutral on binding ones. It never *loses*, which is why it dominates in
aggregate, but the dominance comes entirely from one of the two kinds.

**T10 — restated again.** The residual is not a fixed set of classes. It is
relative to a mechanism's disclosure policy: M22 is residual for commitment-only
adjudication and reachable with full disclosure, at the price of its twin.

## What this does not settle

The boundary is about **evidence-determined** mechanisms, which is every
mechanism in the set by construction. It says nothing about:

- **Entitled mechanisms.** B16c solves both sides of some binding pairs because
  its custodial entitlement means they are not twins for it. That is a larger
  view, not an escape — and its cost is the assumption, which the harness does
  not price.
- **Stateful mechanisms across repeated interactions.** B11 is scored per
  scenario, so its pattern detection cannot show its value here. Whether
  repetition genuinely escapes the boundary or merely shifts the unit of
  analysis is untested, and it is the most interesting remaining question.
- **Anything requiring a party to act rather than assert.** Bonding (T7) and the
  duty to answer (B17) both change incentives rather than evidence. B17 is
  inside the boundary and pays exactly as predicted; bonding was never
  implemented.
