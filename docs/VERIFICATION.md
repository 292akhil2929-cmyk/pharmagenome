# Phase 4 verification

Verified application commit: 52a3bcf8cc4ed5556c4a45648a6a864020f05fed.

- [GitHub Actions run 34205739558](https://github.com/292akhil2929-cmyk/pharmagenome/actions/runs/34205739558): success.
- Backend: Ruff passed, 94 tests passed with PostgreSQL 17; backend Docker build passed.
- Frontend: TypeScript and production build passed; 15 Playwright tests passed.
- Algorithm coverage includes 180 deterministic score comparisons against Biopython 1.88; returned tracebacks independently reconstruct inputs and recompute scores.
- Edge cases cover all-N sequences, overlapping k-mers, multiple FASTA records, invalid symbols, strict scores, local zero-score behavior, deterministic ties and 1,000-by-1,000 alignment.
- Browser coverage includes empty inputs, explicit teaching examples, file input, validation/retry, keyboard tabs, result invalidation, JSON downloads, no-positive alignment and all-N statistics. Previous genomic and workspace regression tests also pass.
- Independent finish review: ship, with no blocking frontend findings after source and desktop/mobile light/dark evidence review.

## Live verification
Anonymous frontend proxy POST checks and Chrome confirmed statistics for AACCGGTTNNACGTACGT: length 18, known bases 16, N 2, GC 50%, AT 50%, 14 valid overlapping 2-mer windows and 3 N-excluded windows.

Global alignment of ACGTACGT versus ACGTCGT returned score 12, seven exact matches, one gap, 87.5% column identity and traceback ACGTACGT / ACGT-CGT. Chrome displayed the full score matrix and highlighted traceback.

Local alignment of TTACGTAA versus GGACGTCC returned ACGT / ACGT, score 8 and 1-based inclusive coordinates 3–6 for both inputs. AAAA versus CCCC returned no positive alignment, score zero and null coordinates. NNNN returned null GC/AT and zero valid k-mers. ACGU was rejected with HTTP 422.

Live Chrome checked statistics, alignment controls, actual results, source hashes, dark theme and 390px mobile containment. The settled document width was 380px within a 390px viewport.

## Evidence boundaries
Browser CI screenshots use explicitly synthetic fixtures and establish layout/interaction behavior, not scientific correctness. Numerical evidence above comes from live computation; independent algorithm comparisons run in backend tests.

JSON download events passed in Chromium CI. A saved live Chrome download is not claimed. The app does not persist submitted sequences to its database; it sends them to the public research API for computation.

Full Docker Compose runtime has not been verified end-to-end. PostgreSQL integration tests and the backend Docker build passed.

Genomic exploration still uses the ten-gene GRCh37 TCGA LUAD SNV subset: 566 profiled samples, 506 unique SNVs and 839 observations. This release adds bounded DNA composition and linear-gap alignment; it does not add clinical annotation, inferential statistics, drug response, ML or AI explanations. See [sequence methods](SEQUENCES.md), [genomic methods](GENOMICS.md) and [source provenance](../DATA_SOURCES.md).
