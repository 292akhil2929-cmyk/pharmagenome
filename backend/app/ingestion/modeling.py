"""Validate and replay the pinned CellMiner modeling snapshot."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "data" / "drug_response"
GENES = ["BRAF", "EGFR", "KRAS", "MET", "NF1", "PIK3CA", "RB1", "STK11", "TP53", "KEAP1"]
LIMITATIONS = [
    "NCI-60 contains about sixty immortalized cancer cell lines; it is not a patient cohort.",
    "Compound activity is an experimental CellMiner average z score, not a dose recommendation or clinical outcome.",
    "The ten genes and ten drugs are a deliberately restricted, predeclared teaching panel.",
    "Expression values combine five platforms; mutation calls summarize protein-function-affecting exome variants.",
]


def optional_number(value, *, binary=False):
    if value == "":
        return None
    number = float(value)
    if not (-1e12 < number < 1e12) or (binary and number not in (0, 1)):
        raise ValueError("Non-finite, out-of-range, or invalid binary value")
    return number


def replay(root=ROOT):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    raw = (root / "cellminer_nci60_curated.csv").read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
        raise ValueError("Curated snapshot checksum mismatch")
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    expected = (["cell_line", "tissue"] + [f"expression_{g}" for g in GENES]
                + [f"mutation_{g}" for g in GENES]
                + [f"response_{d['nsc']}" for d in manifest["drugs"]])
    if not rows or list(rows[0]) != expected or len(rows) != manifest["cell_lines"]:
        raise ValueError("Curated snapshot shape does not match the manifest")
    seen, records, counts = set(), [], {"expression": 0, "mutation": 0, "response": 0}
    for row in rows:
        if not row["cell_line"] or row["cell_line"] in seen or ":" not in row["cell_line"]:
            raise ValueError("Cell-line identifiers must be unique and source-shaped")
        seen.add(row["cell_line"])
        item = {"cell_line": row["cell_line"], "tissue": row["tissue"], "features": {}, "responses": {}}
        for gene in GENES:
            expression = optional_number(row[f"expression_{gene}"])
            mutation = optional_number(row[f"mutation_{gene}"], binary=True)
            item["features"][gene] = {"expression": expression, "mutation": mutation}
            counts["expression"] += expression is not None
            counts["mutation"] += mutation is not None
        for drug in manifest["drugs"]:
            value = optional_number(row[f"response_{drug['nsc']}"])
            item["responses"][drug["nsc"]] = value
            counts["response"] += value is not None
        records.append(item)
    report = {"downloaded": len(rows), "valid": len(rows), "invalid": 0, "duplicates": 0,
              "excluded": 0, "cell_lines": len(rows), **counts}
    return manifest, {"records": records, "report": report}
