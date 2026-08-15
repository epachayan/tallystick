# Findings 08 — Attestation, Relocation, and Level Invariance

> **HISTORICAL RECORD — intentionally frozen.** This finding records an earlier
> phase. Its embedded counts and some standing/open-item language are not current and are preserved
> as part of the correction trail. Current figures: [`../../results/canonical.txt`](../../results/canonical.txt).
> Current claim status: [`../what-is-established.md`](../what-is-established.md).


**Corpus:** v0.9, 650 scenarios, 26 classes, 0 validator violations
**Added:** M24/M25 (attestor twins), `visibility.py`, B16c (custodial) and B16d (digest-only)
**Status:** this document **supersedes an earlier version that over-claimed twice.** Both errors and
their causes are recorded below, because they are the same class of error the project has now made
four times.

---

## The two errors, first

**Error 1 — the paired test used pairs that were not twins.** M19/M10 and M20/M21 were compared as
adversarial/honest twins, but were never seeded together. The adversarial member carried an
out-of-scope action its supposed twin lacked. So the "detection" being measured was of the
overreach, not of the loss or rate ambiguity the pair was meant to isolate.

**Error 2 — the attestor was given custodial power.** B16 read the execution contents even when the
executor's record was unavailable. That is only legitimate if the attestor *holds the contents* —
which makes it a custodian, not an attestor, and assumes the conclusion. Of course the residual
closes if a third party keeps a full copy.

Both errors pushed in the same direction: they made attestation look like it worked.

The fix is now enforced structurally. `src/visibility.py` defines what the adjudicator can actually
see, applying the A3 rule — **availability gates everything else about a record.** If a party cannot
produce its record, the adjudicator learns neither its contents nor whether it was altered.

Under that model all pairs verify as genuine twins:

| pair | identical views |
|---|---|
| M6/M15, M7/M17 | 25/25 |
| M19/M10, M20/M21 | 25/25 |
| M22/M23, M24/M25 | 25/25 |

---

## The corrected result

Paired test — *catch the adversarial class **without** condemning its honest twin*:

| adversarial | honest twin | B16d digest-only | B16c custodial |
|---|---|---|---|
| M19 claimed record loss | M10 genuine loss | **missed** | contradicted ✓ |
| M20 claimed rate | M21 genuine rate | **missed** | contradicted ✓ |
| M22 claimed key compromise | M23 genuine theft | **missed** | missed |
| M24 attestor outage, guilty | M25 outage, honest | **missed** | **missed** |

> **T11 (revised).** Attestation of *existence and integrity* closes **none** of the residual
> classes. A digest-only attestor can prove a record existed and was intact; it cannot say what the
> record contained, so overreach remains unadjudicable. Only **custody** — a third party holding the
> contents — closes the residual, and custody relocates the entire residual to the custodian, which
> equally cannot commit that its own record will remain available (M24, missed 25/25).

This is a **stronger** result than the version it replaces. The earlier claim was "attestation closes
two of three and opens one." The correct claim is:

> The choice is not *attest and be safe*. It is *move the problem to someone else*.

Which is the trusted-third-party bargain the fair-exchange literature has always been explicit
about — and it is why that literature spends so much effort on **reducing** what the TTP must be
trusted with rather than on adding attestors.

---

## T12 — Level invariance (unchanged, and now better supported)

| level | result | indistinguishable pair |
|---|---|---|
| record | T1 | lost record vs. withheld record |
| rate | T7 | unlucky party vs. disciplined offender |
| commitment | T10 | breach of a promise vs. inability to keep it |
| custodian | T11 | custodian outage vs. custodian collusion |

> **T12.** The accuracy/completeness dichotomy recurs at every level of aggregation and delegation.
> Adding a level relocates it. Nothing removes it.

The correction strengthens this. Under the earlier (wrong) reading, attestation partially closed the
residual, which weakly suggested levels could chip away at it. They cannot: the digest-only attestor
— the only kind that does not simply become another party holding the same problem — closes nothing
at all.

### The derived characterisation

T10 enumerated a commitment vocabulary. T12 replaces the enumeration with a rule:

> **A commitment binds iff breaching it is distinguishable from being unable to fulfil it.**

T1's structure, applied to commitments rather than records. *"I will produce my record on demand"* is
well-formed and binds nothing, because breach and incapacity look identical. T10's original criterion
— *facts postdating commitment* — is a **consequence**: future events are precisely those whose
non-occurrence cannot be demonstrated.

**The causal chain, complete.** T12: the dichotomy exists at every level. T11: adding levels moves it
and custody relocates it wholesale. T10: no commitment escapes it. **T8 is what this looks like from
outside** — if the dichotomy cannot be removed anywhere, the only remaining freedom is who pays.

The project began looking for a primitive. It ends with a structural reason no primitive would have
helped.

---

## Standing

| result | status |
|---|---|
| **T11** | **Revised, and strengthened.** Digest attestation closes nothing; custody relocates. |
| **T12** | Unchanged and better supported. |
| **T10** | Re-based on a derived criterion rather than an enumeration. |
| **T8** | Explained as the outside view of level invariance. |
| **T9** | Separate. `key ≡ party` is an independent impossibility, untouched by attestation. |

## Caveats

- Attestor availability is binary. Partial availability, staleness, and attestor compromise are
  unmodelled.
- The regress is argued, not measured — one attestation level was built. A second would test T11's
  prediction directly.
- T12 is four instances with a shared mechanism, not a proof.

## What this episode says about the method

This is the **fourth** time a result has been produced by an artifact rather than a finding, and the
fourth time it was caught by chasing an anomaly rather than reading a summary. The pattern is
consistent: **errors flatter the hypothesis.** Every one of the four made the scheme under test look
better than it was.

The countermeasure that has actually worked is structural, not vigilance: the scenario validator, and
now `visibility.py`. Both convert "remember not to read ground truth" into something the code
enforces. Anything relying on care alone has failed at least once.
