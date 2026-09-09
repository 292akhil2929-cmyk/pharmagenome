# Reproducible analysis bundle

This script exercises the real PharmaGenome computation paths and writes their complete JSON responses to a new output directory. It covers the live system/data manifest, genomic distributions, sequence statistics, Needleman–Wunsch global alignment, a Welch test and repeated cell-line drug-response modeling.

The sequence and measurement values are explicitly synthetic teaching inputs. Genomic and model results come from the selected API's imported datasets and retain dataset, input and code hashes. Nothing in the bundle is medical advice or clinical validation.

From the repository root, with the Docker stack running:

```sh
python examples/reproduce.py --api http://localhost:8000 --out reproduced-analysis
```

Against the public research deployment:

```sh
python examples/reproduce.py --api https://pharmagenome-api.vercel.app --out reproduced-analysis
```

The repeated model evaluation may take longer on a cold deployment. Use `--skip-model` only for a quick computation check. The output directory is intentionally ignored by Git; compare `manifest.json` hashes and complete result files between runs. Model metrics remain deterministic for the same dataset, code revision, fixed parameters and library versions.

Expected structural checks for the pinned release:

- database status is `ready`
- genomics includes a source dataset SHA-256 and profiled-sample denominators
- the Welch result includes the complete submitted groups and an input SHA-256
- the alignment includes score, aligned sequences and traceback metadata
- the model includes a dataset SHA-256, input SHA-256, fixed cross-validation parameters and 177 held-out prediction rows for 59 measured cell lines across three repeats

The last row count is a release check, not a performance or biological claim.
