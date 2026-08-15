"""Semantic validation: is this scenario a possible world?

JSON Schema cannot express any of these. They are cross-field invariants and
mutation semantics, and they belong in code.
"""

from __future__ import annotations

from ..model.types import Party, PartyState


def check(sc: dict) -> list[str]:
    errs: list[str] = []
    sid = sc.get("scenario_id", "?")
    g = sc["ground_truth"]
    auth = sc["authorization"]
    execu = sc["execution"]
    p, e = sc["p_view"], sc["e_view"]

    def bad(msg):
        errs.append(f"{sid}: {msg}")

    dishonest = g["dishonest_party"]
    p_state, e_state = g["p_state"], g["e_state"]

    # -- states must agree with the named dishonest party -------------------
    if dishonest in ("P", "both") and p_state != "dishonest":
        bad(f"dishonest_party={dishonest} but p_state={p_state}")
    if dishonest in ("E", "both") and e_state != "dishonest":
        bad(f"dishonest_party={dishonest} but e_state={e_state}")
    if dishonest == "none" and "dishonest" in (p_state, e_state):
        bad(f"dishonest_party=none but a party state is dishonest "
            f"(p={p_state}, e={e_state})")

    # -- a party that diverges must actually diverge in the record ----------
    diverging = []
    if auth.get("committed") and not auth.get("issued"):
        # Presenting a grant that carries no signature is observable without
        # any content disclosure: the commitment simply is not there.
        if e.get("asserted_auth_issued", True) and e["asserted_scope"]:
            diverging.append("E")
    if auth.get("committed") and auth.get("issued"):
        # Naming an in-scope action as unauthorized is a self-refuting act: the
        # complainant's own chosen query settles it against them.
        if p.get("disputed_action") is not None and p["disputed_action"] in auth["scope"]:
            diverging.append("P")
        if p["asserted_scope"] is not None and p["asserted_scope"] != auth["scope"]:
            diverging.append("P")
        if not p.get("asserted_auth_issued", True):
            diverging.append("P")
        if execu.get("result_delivered") and not p.get("asserted_result_received", True):
            diverging.append("P")
        if not p.get("record_intact", True):
            diverging.append("P")
        if e["asserted_scope"] is not None and e["asserted_scope"] != auth["scope"]:
            diverging.append("E")
        if e.get("record_available", True):
            if not e.get("record_intact", True):
                diverging.append("E")
            if e["asserted_actions"] is not None and \
                    sorted(e["asserted_actions"]) != sorted(execu["actions"]):
                diverging.append("E")
            if [a for a in execu["actions"] if a not in auth["scope"]]:
                diverging.append("E")
        else:
            # Withholding a record you committed to is itself an observable act.
            # It is not a contradiction, but it is not invisible either.
            diverging.append("E")

    if p_state == "mistaken" and "P" not in diverging and p.get("disputed_action") is None:
        bad("p_state=mistaken but the principal's account matches the record")
    if e_state == "mistaken" and "E" not in diverging:
        bad("e_state=mistaken but the executor's account matches the record")

    # -- OPEN-3: invisible misconduct must be declared unadjudicable --------
    # A dishonest party that leaves no observable trace produces a world where
    # abstaining is the correct answer. Scoring that as `correct_abstain` would
    # count ambiguity as resolved when it was merely invisible, so the corpus
    # must mark it unadjudicable and let it score `correct_abstain_amb`.
    if g.get("adjudicable", True):
        for party in ("P", "E"):
            if dishonest in (party, "both") and party not in diverging:
                bad(f"dishonest_party={dishonest} leaves no observable divergence "
                    f"for {party}, so the world must be marked unadjudicable "
                    f"(OPEN-3)")

    # -- adjudicability -----------------------------------------------------
    if not g.get("adjudicable", True) and auth.get("committed"):
        bad("marked unadjudicable while a live commitment exists")
    if not auth.get("committed") and g.get("adjudicable", True):
        bad("no commitment exists but the scenario is marked adjudicable")

    # -- availability gates integrity --------------------------------------
    if not e.get("record_available", True) and e["asserted_actions"] is not None:
        bad("executor cannot produce its record yet asserts its contents")

    # -- the adjudicator ----------------------------------------------------
    adj = sc.get("adjudicator", {})
    if adj.get("colluding") and "favours_blame" not in adj:
        bad("adjudicator colludes but publishes no verdict; nothing to detect")
    if adj.get("favours_blame") and not adj.get("colluding"):
        bad("a published verdict override without collusion is not modelled")
    if adj.get("colluding") and g["dishonest_party"] != "J":
        bad("adjudicator colludes but is not named as the dishonest party")

    # -- key claims ---------------------------------------------------------
    kc = sc.get("key_claim", {})
    if kc.get("genuine") and not kc.get("revoked"):
        bad("a genuine compromise with no revocation claim is not modelled")

    return errs


def validate_corpus(scenarios) -> list[str]:
    out: list[str] = []
    for sc in scenarios:
        out.extend(check(sc))
    return out


def main():
    from ..reporting.harness import load_corpus

    scs = load_corpus()
    errs = validate_corpus(scs)
    if errs:
        seen = {}
        for e in errs:
            seen[e.split(": ", 1)[1]] = seen.get(e.split(": ", 1)[1], 0) + 1
        for msg, n in sorted(seen.items(), key=lambda kv: -kv[1]):
            print(f"  {n:>4}  {msg}")
        raise SystemExit(f"COHERENCE: {len(errs)} violation(s) across {len(scs)} scenarios")
    print(f"coherence: {len(scs)} scenarios internally consistent")


if __name__ == "__main__":
    main()
