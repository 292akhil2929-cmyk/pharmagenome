# Incremental delivery

Phase 1 establishes the foundation. It does not claim the complete master brief is delivered.

| Phase | Scope | Gate |
|---|---|---|
| 1 | PostgreSQL, API, frontend shell, Docker, CI, deployment | Database migration, API integration and browser tests pass |
| 2 | Download, validate, normalize, deduplicate, report | Versioned public dataset, reconciled quality report |
| 3 | Genomics, variant and gene explorers | Correct profiled denominators and filter/pagination tests |
| 4 | Sequence statistics, global/local alignment | Edge cases and known alignment score/traceback tests |
| 5 | Drugs, targets, pathway membership | Source-linked research associations, no recommendations |
| 6 | Hypothesis tests, correlations, enrichment | Null/alternative, assumptions, effect size, correction, reference tests |
| 7 | Drug-response ML | Valid response dataset, group-aware split, CV, multiple metrics |
| 8 | Optional explanation | Verified API model access, server-only key, evidence-constrained output |
| 9 | Full analytical dashboard | Real results, working controls, desktop/mobile accessibility |
| 10 | Full portfolio release | Reproducible demo, documentation, all applicable tests |

No navigation control pretends that a future analytical module already works. Core computational results must not depend on an LLM. A model name configured in this Codex session does not prove availability in the user's OpenAI API account.
