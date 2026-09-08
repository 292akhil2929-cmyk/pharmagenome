# Evidence-constrained research explanations

## Role

Phase 8 adds an optional explanation step after PharmaGenome has computed a statistical or drug-response modeling result. The model is never an analysis engine. The underlying numerical result, method, source, assumptions, limitations and export remain authoritative and usable when explanation is unavailable.

The integration targets `gpt-6-astra` through the OpenAI Responses API. OpenAI's [model guidance](https://developers.openai.com/api/docs/guides/latest-model) identifies that model ID and recommends the Responses API. The [Responses reference](https://developers.openai.com/api/reference/resources/responses/methods/create) documents structured text output, server instructions, token bounds and `store`.

## Request boundary

The frontend constructs a compact evidence envelope from an already-returned application result. It may contain methods, sample counts, estimates, p-values, model metrics, baselines, feature importance, hypotheses, assumptions, limitations and provenance. It excludes raw submitted measurement groups, 2 × 2 input tables, individual cell-line points, sample or person identifiers, ROC coordinates and per-sample predictions. Dataset names, source identifiers and provenance hashes remain in the compact envelope.

The FastAPI endpoint accepts only declared analysis types. It bounds the JSON document to 50 KB, six nesting levels, 300 scalar values, 50 fields per object and 30 items per list. Keys must be short machine-readable identifiers; values must be finite and free of unsupported control characters.

## Generation and verification

The server sends inert evidence rows with stable IDs. Instructions prohibit new calculations, causal inference, clinical claims, treatment recommendations, rounded numbers and unsupported facts. The response must match a strict schema:

- one evidence-bound summary;
- one to four supported findings;
- one to four scope caveats;
- at least one submitted evidence ID for every statement.

After generation, PharmaGenome rejects any evidence ID absent from the request. It also rejects numeric tokens that do not occur in the canonical submitted evidence. Returned metadata includes the model, provider, response ID, generation time and SHA-256 of the compact evidence document. `store` is false.

These checks reduce unsupported output; they do not prove semantic correctness. Users must inspect the cited underlying analysis.

## API and configuration

- `GET /api/research/explain/status` reports model availability without exposing a key.
- `POST /api/research/explain` accepts an analysis type and compact evidence.
- `OPENAI_API_KEY` is optional and backend-only.
- The model ID is fixed to `gpt-6-astra`; the browser cannot select an unverified substitute.

Production currently has no `OPENAI_API_KEY`. The live UI therefore displays “Explanation unavailable,” the POST endpoint returns 503, and no live generated explanation is claimed. To activate the feature, add the key to the backend Vercel project, redeploy, verify the status endpoint returns `available: true`, and test a real explanation against its displayed evidence keys. Do not paste credentials into source code, logs or chat.
