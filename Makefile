SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

.PHONY: check ext-check ext-experiments gate-selftest experiments taxonomy docsync links schema coherence visibility twins coverage conservation declarations pruning staleness unit scorer merkle canonical run sweep clean all

# ---------------------------------------------------------------------------
# One command for correctness, one for research.
#
# `make experiments` depends on `make check`, so a green experiment suite means
# the experiment ran on machinery whose semantics were verified first -- not
# that a script exited with status zero.
# ---------------------------------------------------------------------------

check: gate-selftest schema coherence unit visibility twins coverage conservation declarations pruning docsync links staleness
	@echo
	@echo "== correctness gate passed =="

ext-check:
	@echo "-- a2a_bilateral extension tests (reference library; not part of the correctness gate)"
	@python3 -m pytest src/extensions/a2a_bilateral/tests -q

ext-experiments:
	@echo "-- a2a_bilateral adapter parity (standalone; does not register a protocol)"
	@python3 -m src.extensions.a2a_bilateral.parity

gate-selftest:
	@echo "-- correctness-gate non-vacuity"
	@if (false | true); then \
		echo "ERROR: pipeline failure was masked; pipefail is not active" >&2; exit 1; \
	else \
		echo "pipeline failures propagate"; \
	fi

schema:
	@echo "-- structural validation"
	@python3 -m src.validation.schema

coherence:
	@echo "-- semantic validation"
	@python3 -m src.validation.coherence

unit:
	@echo "-- unit and property tests"
	@python3 -m pytest tests/ -q

scorer:
	@python3 -m pytest tests/test_scorer.py -q

merkle:
	@python3 -m pytest tests/test_merkle.py -q

visibility:
	@echo "-- hidden-field mutation tests"
	@python3 -m src.validation.visibility

twins:
	@echo "-- twin audit"
	@python3 -m src.validation.twins

coverage:
	@echo "-- coverage audit (reports gaps; does not fail the gate)"
	@python3 -m src.validation.coverage | tail -12

conservation:
	@echo "-- conservation boundary"
	@python3 -m src.validation.conservation | tail -8

taxonomy:
	@python3 -c "from src.validation.docsync import write_taxonomy; write_taxonomy()"
	@echo "regenerated docs/taxonomy.md"

docsync:
	@echo "-- generated docs match the code"
	@python3 -m src.validation.docsync

links:
	@echo "-- Markdown links and reachability"
	@python3 -m src.validation.links

declarations:
	@echo "-- declaration audit (derive, then diff)"
	@python3 -m src.validation.declarations | tail -4

pruning:
	@echo "-- protocol pruning (every protocol must be cited by a claim or a question)"
	@python3 -m src.validation.pruning | tail -4

staleness:
	@echo "-- documentation staleness"
	@python3 -m src.validation.staleness | tail -8

# ---------------------------------------------------------------------------

experiments: check run sweep canonical
	@echo
	@echo "== experiments complete; see results/ =="

run:
	@python3 -m src.reporting.run > /dev/null
	@echo "wrote results/summary.txt results/per_class.json"

sweep:
	@python3 -m src.reporting.sweep > results/sweep.txt
	@echo "wrote results/sweep.txt results/sweep.json"

canonical:
	@python3 -m src.reporting.regression > /dev/null
	@echo "wrote results/canonical.txt"

all: experiments

clean:
	@find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache
