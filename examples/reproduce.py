"""Reproduce a small, source-aware PharmaGenome analysis bundle through the public API."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def call(base_url: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        base_url.rstrip("/") + path,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "pharmagenome-reproducer/1.0"},
        method="POST" if body is not None else "GET",
    )
    try:
        with urlopen(request, timeout=120) as response:
            return json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{path} returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach {path}: {exc.reason}") from exc


def write_result(output: Path, name: str, value: dict[str, Any]) -> str:
    filename = f"{name}.json"
    (output / filename).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return filename


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://localhost:8000", help="FastAPI base URL")
    parser.add_argument("--out", type=Path, default=Path("reproduced-analysis"))
    parser.add_argument(
        "--skip-model", action="store_true", help="Skip the slower repeated model evaluation"
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict[str, Any]] = {
        "system": call(args.api, "/api/system"),
        "genomics": call(args.api, "/api/genomics?page_size=10"),
        "sequence_statistics": call(
            args.api, "/api/sequences/statistics", {"sequence": ">tutorial\nAACGTN", "k": 2}
        ),
        "global_alignment": call(
            args.api,
            "/api/sequences/align",
            {"sequence_a": "GATTACA", "sequence_b": "GCATGCT", "mode": "global"},
        ),
        "welch_test": call(
            args.api,
            "/api/statistics/measurements",
            {
                "method": "welch",
                "groups": [[1, 2, 3, 4, 5], [4, 5, 6, 7, 8]],
                "unit": "tutorial units",
            },
        ),
    }
    if not args.skip_model:
        results["drug_response_model"] = call(
            args.api,
            "/api/modeling/evaluate",
            {
                "drug_id": "NSC:718781",
                "algorithm": "logistic",
                "features": ["expression_EGFR", "expression_KRAS", "mutation_count"],
            },
        )

    files = [write_result(args.out, name, result) for name, result in results.items()]
    model = results.get("drug_response_model")
    checks = {
        "database_ready": results["system"]["database"]["status"] == "ready",
        "genomic_dataset_sha256": results["genomics"]["dataset"]["sha256"],
        "welch_input_sha256": results["welch_test"]["input_sha256"],
        "alignment_score": results["global_alignment"]["score"],
        "model_input_sha256": model["input_sha256"] if model else None,
        "model_prediction_rows": len(model["predictions"]) if model else None,
    }
    if not checks["database_ready"]:
        raise RuntimeError("The selected API does not report a ready database.")
    manifest = {
        "kind": "pharmagenome_reproducible_analysis_bundle",
        "generated_at": datetime.now(UTC).isoformat(),
        "api_base_url": args.api,
        "api_version": results["system"]["version"],
        "phase": results["system"]["phase"],
        "files": files,
        "checks": checks,
        "boundaries": [
            "Tutorial sequence and measurement inputs are synthetic and are not biological evidence.",
            "Genomic and modeling results retain their source dataset hashes.",
            "Drug-response modeling is internal cell-line validation, not clinical evidence.",
        ],
    }
    write_result(args.out, "manifest", manifest)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
