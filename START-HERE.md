# Start here

Everything for the Tallystick project is in this repository. Three routes in, depending on why you
opened it.

## I want to understand what this is about

**[`docs/articles/02-general-audience.md`](docs/articles/02-general-audience.md)** - "The Stick
That Was Split in Two". No technical background assumed. Explains the whole thing through medieval
tally sticks: what the problem is, why it can't be fully solved, and what to actually do about it.
About 1,700 words.

## I build agent infrastructure and want the practical version

**[`ARTICLE-MEDIUM.md`](ARTICLE-MEDIUM.md)** - "The Execution Record Is
Not Evidence". The measured findings, the historical argument, the implementation sketch, and the
publication-review correction that caught a masked build failure.

Then **[`README.md`](README.md)** for the repository proper.

## I want to evaluate the research

1. **[`INDEX.md`](INDEX.md)** - the full route map
2. **[`docs/what-is-established.md`](docs/what-is-established.md)** - the claim-strength ledger, in
   three tiers. **Read this before quoting any figure from anywhere.**
3. **[`docs/findings/12-conservation-boundary.md`](docs/findings/12-conservation-boundary.md)** -
   the central result
4. **[`RESEARCH.md`](RESEARCH.md)** - the full record; §12 covers publication readiness
5. **[`docs/test-evidence-map.md`](docs/test-evidence-map.md)** - exactly which tests support each headline result

---

## Two things to check before publishing anything

1. **Add a verified public repository URL only at publication time.** The repository currently
   exists privately at `github.com/epachayan/tallystick`; add that link to the packaged article only
   after it resolves while signed out.
2. **The phase-1 article drafts are now wrong.** They predate the hardening phase and state the
   conservation property unbounded, F01 unscoped, and a claim about M22 that was later refuted. If
   either is already live, it needs correcting or withdrawing.

See [`docs/articles/README.md`](docs/articles/README.md) for publication-specific checks and the
public repository URL caveat.

## Running it

```bash
python3 -m pip install -e ".[dev]"
make check         # thirteen gate stages; must pass before experiments will run
make experiments   # regenerates results/
make taxonomy      # regenerates docs/taxonomy.md from the code
```

Runtime: Python 3.12+, standard library only. Development/test dependency: `pytest`.
CI exercises Python 3.12 and 3.13. Deterministic from seed `20260808`.
