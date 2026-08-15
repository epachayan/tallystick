# Adversarial class taxonomy

**GENERATED from `src/generator.py::M_CLASSES` — do not hand-edit.**
Regenerate with `make taxonomy`. `make check` fails if this file drifts from the
code, because a hand-maintained taxonomy is exactly the artifact that has
carried six of this project's defects (see `RESEARCH.md` §9a).

34 classes, 25 instances each.

| class | family | dishonest | description |
|---|---|---|---|
| M0 | control | none | honest run, no mutation |
| M1 | behavioural | E | executor exceeds granted scope |
| M2 | behavioural | E | executor omits an authorized action, claims completion |
| M3 | record_tampering | E | executor alters its stored copy of the authorization |
| M4 | record_tampering | E | executor alters its stored copy of the execution record |
| M5 | behavioural | P | principal repudiates the authorization entirely |
| M6 | behavioural | P | principal asserts a narrower scope than was granted |
| M7 | behavioural | P | principal denies receiving the delivered result |
| M8 | behavioural | E | executor fabricates an authorization never issued |
| M9 | record_tampering | P | principal alters its stored copy of the authorization |
| M10 | benign_divergence | none | records diverge through loss, neither party dishonest |
| M11 | behavioural | both | both parties misrepresent a committed authorization |
| M12 | no_commitment | both | implicit grant, never committed; parties disagree, unadjudicable |
| M13 | query_abuse | P | principal raises a baseless dispute to probe the committed set |
| M14 | adjudicator_abuse | J | adjudicator colludes with the principal against a correct executor |
| M15 | mistake | none | principal sincerely misremembers the scope it granted (twin of M6) |
| M16 | mistake | none | executor acts in good faith on a stale cached grant (twin of M1) |
| M17 | mistake | none | principal misremembers delivery; result was in fact delivered (twin of M7) |
| M18 | mixed | E | principal misremembers AND executor genuinely exceeded scope |
| M19 | record_tampering | E | executor tampers, then claims the record is simply unavailable |
| M20 | pattern_abuse | E | executor repeatedly claims loss to hide repeated tampering |
| M21 | pattern_benign | none | executor suffers genuine repeated loss at the same observed rate |
| M22 | excuse_abuse | E | executor falsely claims its signing key was compromised, voiding its evidence |
| M23 | excuse_benign | none | a thief with the executor's compromised key performed the out-of-scope action |
| M24 | attestor_abuse | E | executor guilty; the external attestor's own record is unavailable |
| M25 | attestor_benign | none | executor honest; the attestor's record is genuinely unavailable |
| M26 | record_tampering | P | principal alters its stored authorization, then claims it is unavailable |
| M27 | benign_divergence | none | principal genuinely loses its stored copy; nobody is dishonest |
| M28 | pattern_abuse | P | principal repeatedly claims loss to hide repeated tampering |
| M29 | pattern_benign | none | principal suffers genuine repeated loss at the same observed rate |
| M30 | abort_abuse | E | executor acts, then aborts before sending the execution receipt |
| M31 | abort_benign | none | the execution receipt is lost in transit; executor acted correctly |
| M32 | abort_abuse | P | principal aborts before acknowledging a delivered result |
| M33 | abort_benign | none | the delivery acknowledgement is lost in transit |

## Reading this table

`dishonest` names the party whose account is culpably false — `none` marks the
honest twins and controls, which exist so that a mechanism catching the
adversarial class can be checked for catching its innocent counterpart too.

Twin pairings are declared in `src/generator.py::TWIN_OF` and **verified** by
`src/validation/twins.py`; the declaration has been wrong before (F-H3), so the
audit is authoritative, not the list.

Which pairs admit an escape and which do not is derived in
`src/validation/conservation.py` — see `docs/findings/12-conservation-boundary.md`.
