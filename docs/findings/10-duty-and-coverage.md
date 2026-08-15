# 10 — The duty to answer, and a structural gap in the corpus

> **HISTORICAL FINDING.** The recommended next steps in this note were executed by findings 11–13.
> In particular, symmetric withholding was added and the abort caveat was measured. Preserve the
> discussion below as the pre-test reasoning; use [`../what-is-established.md`](../what-is-established.md)
> for current standing claims.

**Date:** 11 August 2026
**Baselines:** `B17_duty_to_answer`, `src/validation/coverage.py`
**Experiments:** 1 (obligation to speak) and 3 (adversarial class generation)

---

## Part 1 — B17: the cleanest conservation result in the project

B13's residual was four classes where the executor asserts nothing. The
proposed fix was an obligation to speak: a party holding a commitment must, on
demand, either open it or answer about the specific item in question. Failing to
do either is a contradiction — not of what it said, but of the duty it accepted
when it signed.

Note what B17 does **not** do. It never reads the withheld record. It treats
non-production as a first-class observable act, which it is: the counterparty
holds E's signature over the execution commitment, so the record's *existence*
is established even when its contents are not. Refusing to open a commitment you
demonstrably made is a different act from never having made one.

### Result

| class | B13 | B17 |
|---|---|---|
| M19 tamper then claim loss | missed | **correct_contradiction** |
| M10 genuine loss | correct_abstain | **false_contradiction** |
| M20 repeated loss as cover | missed | **correct_contradiction** |
| M21 genuine repeated loss | correct_abstain | **false_contradiction** |
| M24 guilty, attestor down | missed | **correct_contradiction** |
| M25 genuine attestor outage | correct_abstain | **false_contradiction** |
| M22 false key-compromise | missed | missed |
| M23 genuine key theft | correct_abstain | correct_abstain |

**24/- before. 24/- after.** Three classes resolved, three honest twins
broken, one for one. 75 misses became 75 false contradictions — the same 75
scenarios, relabelled.

This is the sharpest instance of T8 the corpus has produced, and it is a
*measured* exchange rather than an argued one:

> The duty to speak does not buy resolution. It buys a change of victim.

Under B13 the cost of ambiguity falls on the wronged party: real misconduct goes
unpunished. Under B17 it falls on the honest party who genuinely lost a record:
they are now contradicted for it. **Neither is free, and the harness cannot say
which is preferable — that is a policy question, not a cryptographic one.**

The reason the exchange is exact is worth stating plainly. Non-production is a
single observable, and both worlds produce it. No mechanism reading only that
observable can separate them. B17 does not fail because it is badly designed; it
fails because it is reading a one-bit signal and asking it to carry two bits.

### What B17 does *not* touch

M22, the false key-compromise claim, is unreachable by both. The executor
**does** produce its record — the excuse attacks the signatures, not the
record — so no duty is breached. An obligation to speak is the wrong instrument
for an excuse that operates one level up, on the evidence's validity rather than
its availability.

> **CORRECTED 11 August.** This section originally claimed M22 "has now resisted
> every mechanism in the set" and was "the hardest single class in the corpus".
> That was wrong, and wrong in an instructive way: it was measured across the
> commitment-only family only. The full-disclosure protocols (B1, B3, B9, B10,
> B11, B15, B16c, B16d) all solve M22 — and all fail M23, its honest twin, for
> it. No class in the corpus is unreachable by every mechanism. See
> `docs/findings/12-conservation-boundary.md`; `make check` now recomputes this
> claim rather than trusting the prose.

### Vocabulary earns its keep

B17 wrongs three honest classes but its **false-attribution rate is 0%**,
because it never names anyone. An attributive version of the same mechanism
would have produced 75 false accusations instead of 75 false contradictions.
That is the concrete argument for the non-attributive vocabulary, and it did not
exist before this experiment.

---

## Part 2 — Coverage: the corpus has an executor-shaped hole

Experiment 3 derived the space the classes are meant to span, on the two axes
that determine what an adjudicator can do — what each party **asserted** (which
a commitment can contradict) and what was **withheld** — and checked the
declaration against it.

```
cells occupied by the corpus:  8
structurally possible cells : 106
```

*(Figures as of the 26-class corpus, when the audit was run. The asymmetry it
found is now closed; see finding 11.)*

Most of the 98 unoccupied cells are uninteresting. One is not.

### In the 650-scenario corpus, the principal never withheld its own record. Not once.

```
P withholds its record:   0 / 650
E withholds its record: 150 / 650
```

Withholding is modelled as an executor-only behaviour. This is invisible in the
class list, because no class *says* "the principal always cooperates" — it is a
property of how every class happens to be constructed.

The consequence is direct and it lands on the result above. Constructing the
missing scenario — the principal lies about scope, then declines to produce its
own copy — gives:

```
  B13_witness_messages   missed
  B17_duty_to_answer     missed        (duty does not fire)
```

**B17's duty only ever attaches to the executor**, because that is the only
party the corpus ever asked to produce anything. The mechanism was written
against a corpus with a built-in asymmetry, and inherited it.

This does not overturn the conservation result — the exchange is real and
measured within the classes tested. It does mean B17's 24/- is measured on a
corpus that never asks the mechanism to hold both parties to the same standard.

### The other gap, and why it is smaller

`(E fully silent, record withheld)` is also unpopulated. A constructed instance
behaves as predicted: B13 misses it, B17 catches it. That gap is a missing
*instance* of an already-understood structure, not a missing structure.

The `p_record` gap is different in kind, because no mechanism in the set was
ever given the chance to fail on it.

---

## Standing claims after these two experiments

**T8, conservation — substantially strengthened.** The exchange is exact, in a
new currency (resolution against false contradiction), and it was produced by
trying to *break* the conservation rather than to confirm it. Three independent
denominations now: disclosure bytes, padding overhead, and this.

**B13's "the refuge is silence" — holds, with a correction.** Silence is a
refuge for either party, and the corpus only ever tested one. The claim should
read: *an act remains unattributable when the party performing it makes no
assertion the commitment can contradict, and cannot be compelled to produce.*
B17 shows compulsion is available but not free.

**T10, residual — restated.** M22 is residual for the commitment-only family
only, not for every mechanism. The corrected statement is in finding 12: the
residual is a property of a mechanism's disclosure policy, not an absolute.

**RC-H2, the M-class reconciliation — more urgent.** The taxonomy has now been
shown to carry two defects nothing checked for: a wrong twin declaration (F-H3)
and an unstated single-party asymmetry. Both were found by deriving the
structure and comparing, not by reading the list.

---

## Recommended next

1. ~~**Symmetric withholding classes.**~~ **Done in finding 11.** M26–M29
   establish that the one-for-one duty trade is symmetric across the two parties.
2. ~~**Abort/message-chain failure.**~~ **Done for the modelled shapes in finding 13.**
   M30–M33 measure the receipt/acknowledgement abort and loss legs. A richer channel model and a
   faithful fair-exchange baseline remain open.
3. ~~M22 deserves its own attack.~~ **Superseded.** M22 is solved by the
   full-disclosure family at the cost of M23. It is an ordinary binding twin
   pair, not a special adversary. See finding 12.
