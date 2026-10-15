# Interaction protocols for one intermediary

The multi-hop phase ([finding 14](../findings/14-one-hop.md)) treats a protocol as a declared
interaction specification, not as adjudication code. This page is the prose account. The message
tables are generated from `specs/*.toml` into [specs.md](specs.md), and `make check` fails if they
drift.

## Roles and objects

- **P**, the principal, delegates to **I**, the intermediary, which sub-delegates to **E**, the
  executor. I reports the execution back to P.
- A committed object is a set with a Merkle commitment root:
  - **G**, the scope P grants to I
  - **S**, the scope I sub-delegates to E
  - **X**, the actions E executed
  - **R**, the actions I reports to P
- A message **binds** an object when it carries that object's root under the sender's signature.
  A party **holds** a copy of a signed message when it received it directly or when it arrived
  forwarded inside another message.

## The specification is the protocol

Each `[[message]]` in a specification declares:

| field | meaning |
|---|---|
| `from`, `to` | sender and receiver |
| `signed` | whether the sender signs it; an unsigned message binds nothing |
| `binds` | which objects' commitment roots it carries |
| `forwards` | earlier messages it carries along; the receiver then holds copies of those too |
| `requires` | messages the sender must already hold before sending it |
| `checks` | what an honest receiver verifies before accepting it: `subset:A:B` or `equal:A:B` |

The harness does not hard-code the flow. Which signed copies exist in a scenario, and who holds
them, is derived from the specification and the scenario's record of which messages were sent
(`src/multihop/spec.py`). So changing what a protocol carries means editing a specification, and
the adjudicator stays as it is. `B13_hop3` and `B13_chain3` share one adjudicator for exactly this
reason.

## The three specifications

**`bearer3`** is the deployed default: bearer tokens and each party's own log. Nothing is signed by
a counterparty, so the adjudicator can see that the parties disagree but cannot hold anyone to a
prior statement.

**`hop3`** applies bilateral commitment to each link separately. Every message is signed and
acknowledged, but each signature binds only its own object, nothing is forwarded, and I's report
is I's own restatement of the execution. Each hop is accountable. The chain as a whole is not.

**`chain3`** adds four things to `hop3`:

1. The sub-grant forwards P's signed grant and binds G as well as S. E can check S ⊆ G before
   acting, and E holds P's signature.
2. E's acknowledgement binds (S, G), and its execution receipt binds (X, S). A receipt says which
   grant it was executed under.
3. I's report forwards E's acknowledgement and execution receipt. P then holds signatures from a
   party it never deals with directly.
4. The report must equal the execution (`equal:R:X`). I may forward what happened, but not restate
   it.

## What `make check` verifies

`src/multihop/conformance.py`:

1. Every specification is internally consistent. It cannot forward a message the sender never
   holds, require one that has not been declared, or bind from an unsigned message.
2. **Ordering.** No scenario sends a message before the messages it requires, under any
   specification.
3. **Confinement.** The copies each adjudicator receives are exactly the ones its specification
   yields. This is derived a second, independent way and diffed.
4. **Visibility.** Mutating ground truth and class labels moves no verdict.
5. **Prevention.** The classes an honest receiver would refuse under each specification are derived
   and diffed against the declaration.

`src/multihop/boundary.py` derives which class pairs are evidential twins under which
specification, and checks the conservation boundary against brute force.

## Adding a specification

Write `specs/<name>.toml`, add the name to `SPEC_NAMES` in `src/multihop/spec.py`, register an
adjudicator against it in `src/multihop/protocols.py`, and run `make spec-doc` and `make check`. If
the new protocol changes which pairs are twins or which classes are prevented, the gate will say
so. Update `EXPECTED_TWINS` or `EXPECTED_PREVENTED` deliberately, never to make the gate pass.

## Relation to multiagent interaction-protocol work

The specification format was written for this harness, but it sits in a recognisable line of
multiagent-systems work, and the differences are the point.

**Information protocols (BSPL).** Singh's BSPL declares a protocol as roles, messages and
parameters, with each parameter adorned as supplied from outside (`in`), produced (`out`) or
possibly unbound (`nil`). Message order is not written down; it follows from which bindings a
message needs before it can be sent. Its properties are about correct enactment: integrity of
bindings, uniqueness per key, immutability, and the absence of ordering, knowledge and occurrence
conflicts [1]. The specifications here are close in spirit and simpler in form:

| here | nearest BSPL notion | difference |
|---|---|---|
| `from`, `to` | roles and messages | same idea |
| `binds` | the parameters a message carries | here only commitment roots, and only under a signature |
| `requires` | causality from `in` dependencies | here written as explicit predecessor messages, not derived from information |
| holdings derived from `to` and `forwards` | a role's local view of bindings | here the view is an evidential record that a party may withhold or fabricate |
| `checks` | integrity constraints | here enforced by an honest receiver, which yields prevention |

BSPL assumes agents enact the protocol. Tallystick assumes they may lie, withhold, abort or
collude, and asks a different question of the same kind of declaration: from the copies each
party can produce, what can an adjudicator correctly conclude, and when can it name who diverged?

**Commitment protocols.** Commitment-based work gives messages a normative meaning: who owes what
to whom, and how that evolves [2]. Chopra and Singh show that a debtor's and a creditor's views of
a commitment can diverge through asynchrony alone, and give message patterns and semantics that
restore alignment, explicitly setting trust aside [3]. That divergence is the analogue here of a
*mistaken* party (an honest account that differs from the record). The dishonest case, which the
alignment work rules out by assumption, is where the twins and the boundary in finding 14 live.

**Computational accountability.** Baldoni and colleagues treat accountability as a directed
relation, built into an agent organisation through commitments made when an agent adopts a role
or accepts a goal (the ADOPT protocol) [4]. That work designs who answers to whom. This harness
measures what the evidence a protocol leaves behind can establish when the parties disagree about
whether the account was kept.

**Open in this direction.** Expressing `hop3` and `chain3` in BSPL and deriving holdings from BSPL
role views rather than from `forwards`; asking whether BSPL's enactment analysis can be extended
with an evidential layer, so that a specification can be checked for which twins it admits; and
connecting the mistaken/dishonest split to commitment alignment, where honest divergence already
has a theory.

1. M. P. Singh. Information-driven interaction-oriented programming: BSPL, the Blindingly Simple
   Protocol Language. *AAMAS 2011*, 491-498.
2. M. P. Singh. An ontology for commitments in multiagent systems: toward a unification of
   normative concepts. *Artificial Intelligence and Law* 7 (1999), 97-113.
3. A. K. Chopra and M. P. Singh. Multiagent commitment alignment. *AAMAS 2009*.
4. M. Baldoni, C. Baroglio, K. M. May, R. Micalizio and S. Tedeschi. Computational accountability
   in MAS organizations with ADOPT. *Applied Sciences* 8 (2018), 489.

These readings are summaries for orientation, not a survey. Check them against the papers before
citing.
