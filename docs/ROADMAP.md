# Incremental delivery

Phases 1–7 are delivered. Phase 8's server-only GPT-6 Astra integration, evidence contract and unavailable state are delivered; live generation remains gated on a configured API key and verified model access. It does not claim the complete master brief is delivered.

| Phase | Scope | Gate |
|---|---|---|
| 1 | PostgreSQL, API, frontend shell, Docker, CI, deployment | Database migration, API integration and browser tests pass |
| 2 | Download, validate, normalize, deduplicate, report | Versioned public dataset, reconciled quality report |
| 3 | Genomics, variant and gene explorers | Correct profiled denominators and filter/pagination tests |
| 4 | Sequence statistics, global/local alignment | Edge cases and known alignment score/traceback tests |
| 5 | Drugs, targets, pathway membership | Source-linked research associations, no recommendations |
| 6 | Hypothesis tests, correlations, enrichment | Null/alternative, assumptions, effect size, correction, reference tests |
| 7 | Drug-response ML | Delivered: aligned CellMiner data, repeated stratified CV, baseline, multiple metrics, held-out importance |
| 8 | Optional explanation | Integration delivered; production generation awaits server-only API access verification |
| 9 | Full analytical dashboard | Real results, working controls, desktop/mobile accessibility |
| 10 | Full portfolio release | Reproducible demo, documentation, all applicable tests |

No navigation control pretends that a future analytical module already works. Core computational results must not depend on an LLM. A model name configured in this Codex session does not prove availability in the user's OpenAI API account.
