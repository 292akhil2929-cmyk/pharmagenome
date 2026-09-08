import argparse
import json
from pathlib import Path

from app.ingestion.normalize import normalize
from app.ingestion.snapshot import SNAPSHOT, download, read_snapshot

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=SNAPSHOT)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    if not args.replay:
        download(args.output)
    manifest, payload = read_snapshot(args.output)
    result = normalize(payload)
    processed = args.output / "processed"
    processed.mkdir(exist_ok=True)
    (processed / "normalized.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (processed / "report.json").write_text(json.dumps(result["report"], indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result["report"].items() if k != "rejected_records"}, indent=2))
    if result["report"]["invalid"]:
        raise SystemExit("Invalid records found. Review the report before promoting this snapshot.")
