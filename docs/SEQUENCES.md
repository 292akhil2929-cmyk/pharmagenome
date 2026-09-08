# DNA sequence methods

Phase 4 implements deterministic sequence statistics and pairwise alignment without a database or language model. These are research algorithms, not variant calling, clinical interpretation or a genome-scale aligner.

## Input and privacy
Paste text or choose one local FASTA/plain-text file per sequence. The browser reads the file as text and submits it to the research API. The application does not persist the sequence in its database. This public service has no private clinical-data workflow.

Normalization removes whitespace, uppercases letters and drops one leading FASTA header. Only A, C, G, T and N are accepted; multiple records, RNA U, gaps and other ambiguity symbols are rejected. The normalized sequence and its SHA-256 are included in the downloadable JSON.

Statistics accept up to 100,000 normalized bases (200,000 raw characters). Alignment accepts up to 1,000 bases per sequence (5,000 raw characters each). Browser file limits use bytes. The server proxy caps the full JSON request at 250,000 bytes and times out after 20 seconds.

## Composition and k-mers
Length and composition counts include N. GC and AT percentages divide by the count of known A/C/G/T bases; both are null for all-N input. Composition percentages divide by the full normalized length.

For k from 1 through 6, enumerate overlapping forward-strand windows. Windows containing N are excluded from k-mer frequencies and counted separately. Frequencies divide by valid windows, not all windows. Reverse complements are not merged. If k exceeds length, there are zero windows. Results sort by descending count then lexical order; the interface paginates 20 rows while JSON exports include every k-mer.

## Global and local alignment
The Python implementation computes Needleman-Wunsch global and Smith-Waterman local alignment directly using dynamic programming and linear gap penalties. Defaults: match +2, mismatch -1, gap -2. Allowed integer ranges: match 1–10, mismatch -10–0, gap -10–-1. N always receives the mismatch score, including N versus N.

Global alignment includes both full inputs and penalizes terminal gaps. Local alignment floors scores at zero and traces back from the highest-scoring cell to zero. A local result with no positive score has empty alignment strings and null coordinates.

Ties prefer diagonal, then up, then left. Local endpoint ties use the first maximum in row-major order. Other correct implementations may choose a different optimal traceback with the same score.

Coordinates are 1-based inclusive in normalized inputs. Identity is exact A/C/G/T matches divided by all alignment columns, including gap and N columns; zero columns produce null identity. Markers distinguish exact matches (|), substitutions (.), unknown-base comparisons (?) and gaps (space).

Time and traceback memory are O(n*m); score computation retains two rolling rows. The educational score matrix is returned only when both sequences have at most 20 bases; larger accepted sequences still return full alignments. This is not an affine-gap or genome-scale aligner.

## API
POST /api/sequences/statistics:
```json
{"sequence":">example\nAACCGGTTNNACGTACGT","k":2}
```

POST /api/sequences/align:
```json
{"sequence_a":"ACGTACGT","sequence_b":"ACGTCGT","mode":"global","match":2,"mismatch":-1,"gap":-2}
```

Responses include normalized inputs, computed result, parameters, method/version, UTC computation time, code revision and limitations. Invalid input receives 422 with a sanitized message. Unknown fields and non-integer scores are rejected. The frontend proxies fixed operation names only; API credentials are not required.

## Validation
Tests compare 180 deterministic short global/local alignment scores with Biopython PairwiseAligner across three scoring configurations, including N substitution rules. They independently reconstruct input substrings and recompute returned traceback scores. Additional cases cover coordinate boundaries, ties, no positive local score, overlapping k-mers, all-N input, invalid FASTA, strict parameters and the 1,000-by-1,000 input boundary.

Reference: [Biopython pairwise alignment documentation](https://biopython.org/docs/latest/Tutorial/chapter_pairwise.html). Biopython 1.88 is a test dependency only; production uses the direct implementation.
