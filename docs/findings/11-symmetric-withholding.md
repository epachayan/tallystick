# 11 — Symmetric withholding: the conservation is structural

> **HISTORICAL FINDING.** This note records the 30-class stage. Four abort/loss classes were added
> immediately afterward in finding 13. The one-for-one withholding result remains valid; current
> figures and limitations are in [`../what-is-established.md`](../what-is-established.md).

**Date:** 11 August 2026
**Closes:** RC-H9, RC-H11
**Corpus at this finding:** 30 classes / 750 scenarios (was 26 / 650)

---

## What was wrong

In the 650-scenario corpus the principal never withheld its own record. Not
once, against the executor's 150. No class *said* "the principal always cooperates" — it was a
property of how every class happened to be built, invisible in the class list.

Four classes close it, mirroring the two existing loss/tamper twin pairs with
the roles reversed:

| class | |
|---|---|
| M26 | principal alters its stored authorization, then claims it is unavailable |
| M27 | principal genuinely loses its stored copy; nobody is dishonest |
| M28 | principal repeatedly claims loss to hide repeated tampering |
| M29 | principal suffers genuine repeated loss at the same observed rate |

M27/M26 and M29/M28 are evidence-identical under both disclosure policies,
verified by the twin audit and pinned by test. The scaffolding for this already
existed — `p_available` and `p_intact` were threaded through the generator and
simply never set — which is a fair measure of how easy the asymmetry was to
miss.

## What it exposed

**B17's duty was one-sided.** On the new classes it did not fire at all:

```
  M26  missed        M27  correct_abstain
  M28  missed        M29  correct_abstain
```

The mechanism held only the executor to its commitment, because that was the
only party the corpus ever asked to produce anything. It inherited the
asymmetry rather than choosing it. Same for `B11_stateful`, whose pattern
detector read `e_disputes` and had no notion that a principal could have a
history at all.

Both are now symmetric. The executor holds P's signature over the authorization
commitment, so the grant's existence is established even when P will not produce
its copy — the same duty, the same breach, the other party.

## The result, after the fix

*(Figures as of the 30-class corpus. Four abort classes were added later; see
finding 13. `results/canonical.txt` is authoritative.)*

| | B13 | B17 |
|---|---|---|
| full-class | 24/- | 24/- |
| false attribution | 0% | 0% |
| miss rate | 20.0% | 3.3% |
| fails | M19 M20 M22 M24 **M26 M28** | M10 M21 M22 M25 **M27 M29** |

Five guilty classes resolved, five honest twins broken. **Exactly one for one,
on both sides of the relationship.** 125 misses become 125 false contradictions.

The earlier three-for-three result could have been an artifact of an
executor-shaped corpus. It was not. The exchange is a property of the structure:

> Non-production is a one-bit signal. Both worlds emit it. A mechanism reading
> only that bit cannot carry two bits of information — and it does not matter
> which party is doing the withholding.

That is a materially stronger claim than the one in finding 10, and it was
purchased by looking for the thing that would have falsified it.

## Two things worth carrying forward

**B13 was never executor-specific; the corpus was.** Its residual now contains
principal-side classes, and the characterisation is unchanged and cleaner: in
every failing class, *some* party is silent about the artifact in dispute. The
residual tracks silence, not role.

**The non-attributive vocabulary earns its keep twice over.** B17 now wrongs
five honest classes and its false-attribution rate is still 0%, because it never
names anyone. An attributive version would have produced 125 false accusations.

## What did not move

**F01 survives the corpus change unchanged.** B0 0/100, B1 100/100 on the
principal-liar classes. Four new classes, 100 new scenarios, no effect — as it
should be, since none of them touch the regression structure.

**M22 is untouched by the new classes**, as expected: the executor produces its
record there, so no duty is breached and principal-side withholding is
irrelevant to it. (The stronger claim in finding 10 — that M22 resists *every*
mechanism — was wrong and is corrected in finding 12. It is solved by the
full-disclosure family at the cost of M23, which makes it an ordinary binding
twin pair.)

## Method note

This is the second time deriving a structure and checking the declaration
against it has found a defect nothing else caught — F-H3 for the twin
declaration, RC-H9 for the withholding asymmetry. Both were properties of the
corpus that no test asserted because no one thought to state them. `make check`
now reports withholding counts by party, so this particular asymmetry cannot
silently return.

The general lesson is uncomfortable and worth writing down: **a hand-built
taxonomy encodes assumptions its author never stated, and the only reliable way
to find them is to enumerate the space it claims to cover and diff.** Every
remaining hand-maintained declaration in the repo is suspect by the same
argument.
