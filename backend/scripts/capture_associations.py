import argparse
import json
from pathlib import Path

from app.ingestion.associations import capture, replay

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    manifest, data = replay(args.output) if args.replay else capture(args.output)
    print(json.dumps({"sha256": manifest["sha256"], "report": data["report"]}, indent=2))
    if data["report"]["invalid"]:
        raise SystemExit("Invalid records require review")
