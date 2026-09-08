import argparse
import json
from pathlib import Path

from app.ingestion.load import load_snapshot
from app.ingestion.snapshot import SNAPSHOT

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    args = parser.parse_args()
    print(json.dumps(load_snapshot(args.snapshot), indent=2))
