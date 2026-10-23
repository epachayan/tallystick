# The nine existing three-party dispute classes, in plain language

Source of truth: `src/multihop/generator.py` (`H_CLASSES`, `make_scenario`) in Tallystick v0.11.1. This index is a **human-readable taxonomy**, not protocol-specific test vectors, and does not replace the seeded `corpus/multihop.v0.1.jsonl`.

The roles are **P** (principal), **I** (intermediary), and **E** (executor). In the last column, "diverges" means an account differs from the record; it does **not** always imply dishonesty. The underlying generator also distinguishes genuine mistakes from deliberate dishonesty.

| ID | A recognizable dispute | Accounts that diverge | Honest mistake? | Evidence question for a standards author |
|---|---|---|---|---|
| H1 | Everybody acts within scope and reports consistently | None | No | Can the mechanism establish an ordinary clean chain without inventing blame? |
| H2 | I widens E's instructions beyond P's original grant, then denies widening them | I | No | Can E see and verify P's original authorization before acting? |
| H3 | I mistakenly widens the delegated instructions while sincerely recalling a narrower scope | I | Yes (I) | Does the verdict distinguish contradiction from intent? |
| H4 | E overreaches; E is unavailable and I genuinely lost E's acknowledgement | E | No | Can anyone recover the signed instruction context without I's missing copy? |
| H5 | I widens instructions, hides E's acknowledgement, and claims it was lost; E is unavailable | I | No | Can the evidence distinguish this from H4? |
| H6 | I and E jointly fabricate a consistent cover account for an unauthorized action | I and E | No | Is there independent service-side evidence beyond the colluding chain? |
| H7 | P sincerely blames the chain for an outside effect that the chain never caused | P | Yes (P) | Does the protocol avoid declaring malicious execution merely from a complaint? |
| H8 | P and I re-sign a narrower grant afterward to accuse E of an authorized action | P and I | No | Does E hold the original P-signed authorization? |
| H9 | I actually sub-delegates outside P's authorization and blames E | I | No | Can the original grant and subgrant be distinguished after the dispute? |

## How to use with an external draft

For each case and each version-pinned draft, list **only the artifacts that draft mandates**. Then determine which party can obtain each artifact *after* the failure/collusion scenario. Mark a case `N/A` where its message type or threat actor does not exist in the draft. Only compare verdicts after projecting those available artifacts; a valid signature on an executor's claim is not necessarily a true execution observation.

Do not treat an agent's reachability, the presence of a token, or the declared existence of a receipt as proof that a third party can actually produce it. Do not score applicability as success. Do not claim one of the original Tallystick B13 outcomes as a result for any external standard.
