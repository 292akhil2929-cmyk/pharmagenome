import json

from app.ingestion.load_associations import load_snapshot

if __name__ == "__main__":
    print(json.dumps(load_snapshot(), indent=2))
