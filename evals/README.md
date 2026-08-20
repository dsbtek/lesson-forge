# evals/

Offline evaluation suites for the agent pipeline: golden lesson requests, rubric
scoring of generated lessons, standards-alignment checks, and regression fixtures
for the deterministic validator.

Phase 1 ships the deterministic validator (`app/agents/validator.py`) and its unit
tests under `apps/api/tests/`. A broader LLM-output eval harness lives here in a
later phase.
