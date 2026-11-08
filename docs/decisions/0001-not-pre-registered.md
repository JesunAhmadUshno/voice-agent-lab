# 0001: Label the study not pre-registered; no commit is the lock

Date: 2026-11-08. Status: accepted. Decided under the portfolio standard v2.

## Context

The standard tags a proposal as proposal-v1 only when git history proves
the plan came before any code or result. The first commit (cdf3a35,
2026-11-04) holds SPEC.md before any code, but it states scope and
level-closing criteria only: no hypotheses and no pass lines. The Build
and Deep designs (BUILD-SPEC.md, DEEP-SPEC.md) say "written before the
code", and they set the 5 ms, 100 ms and 500 ms budgets, but each was
committed in the same commit as its results (873fc4f, fd97883), so git
cannot show they came first.

## Decision

No proposal-v1 tag. The repo carries the "not pre-registered" label and
is capped at Functional. PROPOSAL.md gathers the plan as written and is
marked not locked. REPORT.md scores the stated budgets as exploratory
criteria, not as locked hypotheses.

## Consequences

Evaluated and v1.0 Released need a new proposal, locked by tag before
its first run, and a confirmatory run under it. Inventing a lock after
the results exist is ruled out.
