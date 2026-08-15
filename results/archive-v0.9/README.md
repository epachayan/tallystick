# Archived results — pre-hardening (v0.9)

Outputs of the code as it stood before the hardening refactor. Kept as a record
of what was believed, **not** as reference figures. The code that produced them
no longer exists.

| file | what it was | why it is not current |
|---|---|---|
| `audit.txt` | leak check | **This is the audit that reported every baseline "clean" while `B7_verifiable_adjudication` was reading `adjudicator.colluding`.** It looked for suspicious reads instead of making them impossible. Replaced by `src/validation/visibility.py`, which mutates each hidden field and requires the verdict not to move. |
| `scorer_audit.txt` | scorer sweep | Ran against the pre-correction scorer, whose branch order let a mechanism's vocabulary decide the label before adjudicability. Note it records `correct_abstain_amb` as never produced — that was the bug, not a property. |
| `merkle.txt` | proof size table | Sizes from a module that built proofs and never verified one. Encoding has since changed (cardinality bound into the root, orientation derived rather than carried). |
| `experiments.txt` | E1–E12 output | Superseded by `results/summary.txt`, `sweep.txt`, `canonical.txt`. |
| `v0.9-*.json/.txt` | pre-hardening canonical figures | Retained for reproducible historical comparison. |

`audit.txt` is the most instructive file here. It is what a passing audit looks
like when the audit is the wrong shape.
