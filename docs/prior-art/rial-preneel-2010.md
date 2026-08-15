# Reading Note — Rial & Preneel, *Optimistic Fair Priced Oblivious Transfer* (AFRICACRYPT 2010)

**Read:** 8 August 2026, from the paper and the authors' presentation
**Verdict:** three insights, one of which **partly inverts the design conclusion of this project.**

---

## I1 — Verifiability by construction beats disclosure minimisation

The finding that matters most. Their adjudicator does **not** query the parties or receive
redacted evidence. It verifies the *protocol messages themselves*, and the protocol is built so
that:

> `POTVerReq` does not need the vendor's secret key.
> `POTVerResp` does not need the buyer's choice τ.

Correctness of a request and a response is **publicly verifiable without any private input**. The
adjudicator learns nothing during a dispute not because disclosure was minimised, but because
there was never anything to disclose.

**Why this bites.** B2 → B4 → B5 → B6 all treat disclosure as a **dial turned at dispute time**:
how much of the record do we hand over, and can we substitute proofs for contents? T3's crossover
formula is entirely an artifact of that framing — it asks when proving is cheaper than telling.

Rial & Preneel show the dial can be removed. Design the message format so correctness carries its
own public witness, and disclosure at adjudication is **zero by construction**; the crossover
question does not arise.

> **T3 is not wrong, but it answers a question a better protocol design does not have to ask.**

This should be stated plainly in the write-up. It is the strongest argument that the harness has
been optimising within a frame rather than choosing the frame — the same criticism the
critical review levelled at the tally-stick metaphor, recurring one level down.

**What it would take to test:** an M-class where the executor's *request* and the principal's
*grant* each carry a public correctness witness, and a baseline whose adjudicator verifies
witnesses rather than inspecting records. If disclosure goes to zero while coverage holds, the
whole selective-disclosure line (B2–B6) is superseded rather than refined.

---

## I2 — Powerless beats accountable

Their stated property: privacy holds **even if the adjudicator is corrupted.** `A` and `V` cannot
learn τ; `A` and `B` cannot learn non-purchased messages.

Compare B7, which answers adjudicator collusion (M14) by publishing a recomputable transcript —
making the adjudicator *accountable* for what it does with what it learns. Rial & Preneel make the
adjudicator *incapable* of learning it in the first place.

> **Powerless beats accountable.**

This inverts the through-line the project ran on. Every effective fix here worked by taking a
trusted party and making it accountable — the verdict state (B3), the complainant (B6), the
adjudicator (B7). Rial & Preneel demonstrate the superior move: **remove the need to trust the
party at all**, by making the verification public and the private inputs structurally unavailable.

Accountability is what you reach for when you cannot achieve incapacity. It is the second-best
answer, and this project treated it as the only one.

---

## I3 — A *compelling* adjudicator, and independent confirmation of T8

Their dispute flow is not passive. When the buyer complains, `A` **verifies the request and sends
it to the vendor**, and the vendor must return a response for `A` to verify. The adjudicator can
compel production; the fair-exchange family generally resolves non-response by timeout and ruling
against the silent party, which is how it obtains its timeliness guarantee.

Every baseline here models `A` as passive — it sees only what is volunteered. That is an
unsurfaced assumption, and it directly affects **T5**: if non-production is a protocol violation
with a defined consequence rather than a misfortune earning suspicion, then claiming loss no
longer dominates tampering.

**But the escape is not free, and this is the useful part.** Ruling against the silent party also
rules against the party that genuinely lost its record. Fair exchange accepts that cost knowingly,
in exchange for termination.

> That is precisely a **T8 denomination** — the ambiguity paid for in false accusation of the
> unlucky — reached independently, in a different literature, twenty-five years earlier.

**T8 is confirmed from outside this project's framing.** A mature protocol family, given the same
impossibility, chose one of the four currencies and paid it deliberately. That is the strongest
external evidence the conservation property is real rather than an artifact of these baselines.

---

## Consequences for the write-up

| item | change |
|---|---|
| **T3** | Reframe. It answers a question that verifiability-by-construction dissolves. Keep as a result about *this* design space, not about disclosure generally. |
| **Through-line** | Demote. "Make the trusted party accountable" is the second-best move; "make it incapable" is first. Say so. |
| **T5** | Add the passive-adjudicator assumption explicitly. A compelling adjudicator with timeout semantics escapes the refuge — at a T8 cost. |
| **T8** | **Strengthen.** Independent confirmation from the fair-exchange family. This is now the best-supported result in the project. |
| **T2** | Unchanged. Their guarantee concerns what the *adjudicator* learns; T2 bounds what the *complainant* learns. Still distinct. |

## New baseline suggested

**B13 — witness-carrying messages.** Grant and execution each carry a publicly verifiable
correctness witness; the adjudicator checks witnesses and never inspects records. Predicted:
disclosure → 0 at full coverage, superseding B2–B6. If it holds, it is the single most useful
thing left to build.

## Still unread

Kremer, Markowitch & Zhou (2002), *An intensive survey of fair non-repudiation protocols* — and
after this, its priority rises. If one paper from this family overturned a design conclusion, the
survey of the whole family is likely to hold more. Its documented attacks on fairness and
termination are also free M-classes.
