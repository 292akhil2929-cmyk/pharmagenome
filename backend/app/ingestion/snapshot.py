"""Official public-source snapshot acquisition. Raw response bytes are immutable."""
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

STUDY = "luad_tcga_pan_can_atlas_2018"
PROFILE = STUDY + "_mutations"
SAMPLE_LIST = STUDY + "_sequenced"
GENES = [673, 1956, 3845, 4233, 4763, 5290, 5925, 6794, 7157, 9817]
BASE = "https://www.cbioportal.org/api"
SNAPSHOT = Path(__file__).resolve().parents[2] / "data" / "luad_snv"
LIMITATIONS = [
    "Ten selected genes only; not an exome-wide mutation catalogue.",
    "Only unambiguous single-nucleotide variants are loaded. Other types are reported as excluded.",
    "Profile membership does not establish per-base callability or confirm a wild-type genotype.",
    "Coordinates are GRCh37/hg19. No liftover or reference-sequence allele verification is performed.",
    "VAF is calculated from tumour alternate and reference read counts, not population frequency.",
    "Gene symbols and types come from cBioPortal; full gene names and gene coordinates are not supplied.",
    "No drug, pathway, response, statistical, predictive or clinical conclusions are supplied by this import.",
]


def digest_manifest(files):
    text = "\n".join(f"{name}:{files[name]['sha256']}" for name in sorted(files))
    return hashlib.sha256(text.encode()).hexdigest()


def download(root=SNAPSHOT):
    root = Path(root)
    if (root / "manifest.json").exists():
        raise ValueError("Snapshot already exists. Choose a new output directory; never overwrite provenance.")
    raw = root / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    endpoints = {
        "study.json": f"{BASE}/studies/{STUDY}",
        "profile.json": f"{BASE}/molecular-profiles/{PROFILE}",
        "sample_ids.json": f"{BASE}/sample-lists/{SAMPLE_LIST}/sample-ids",
        "samples.json": f"{BASE}/studies/{STUDY}/samples?projection=DETAILED&pageSize=1000&pageNumber=0",
        "assembly.json": "https://grch37.rest.ensembl.org/info/assembly/homo_sapiens?content-type=application/json",
    }
    for gene in GENES:
        endpoints[f"gene-{gene}.json"] = f"{BASE}/genes/{gene}"
        endpoints[f"mutations-{gene}.json"] = (
            f"{BASE}/molecular-profiles/{PROFILE}/mutations?sampleListId={SAMPLE_LIST}"
            f"&entrezGeneId={gene}&projection=DETAILED&pageSize=100000&pageNumber=0"
        )
    files = {}
    for name, url in endpoints.items():
        for attempt in range(3):
            try:
                request = Request(url, headers={"Accept": "application/json", "User-Agent": "PharmaGenome/0.2"})
                with urlopen(request, timeout=45) as response:
                    body = response.read(20_000_001)
                    if len(body) > 20_000_000:
                        raise ValueError("Response exceeded the snapshot size limit")
                    parsed = json.loads(body)
                    count = response.headers.get("total-count")
                    if count and isinstance(parsed, list) and int(count) != len(parsed):
                        raise ValueError(f"Truncated response: {name}")
                break
            except (HTTPError, URLError, TimeoutError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        (raw / name).write_bytes(body)
        files[name] = {"url": url, "sha256": hashlib.sha256(body).hexdigest(),
                       "bytes": len(body), "retrieved_at": datetime.now(UTC).isoformat()}
    manifest = {
        "schema_version": 1, "study_id": STUDY, "profile_id": PROFILE,
        "sample_list_id": SAMPLE_LIST, "selected_gene_ids": GENES, "is_fixture": False,
        "retrieved_at": datetime.now(UTC).isoformat(), "files": files,
        "sha256": digest_manifest(files), "limitations": LIMITATIONS,
        "license": "ODC Open Database License; cite cBioPortal and TCGA, Cell 2018.",
        "license_url": "https://docs.cbioportal.org/user-guide/faq/",
        "assembly_source": "Ensembl GRCh37 REST assembly metadata",
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def read_snapshot(root=SNAPSHOT):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    expected = {"study.json", "profile.json", "sample_ids.json", "samples.json", "assembly.json"}
    expected |= {f"{kind}-{gene}.json" for gene in GENES for kind in ["gene", "mutations"]}
    if (manifest.get("schema_version") != 1 or manifest.get("study_id") != STUDY
            or manifest.get("profile_id") != PROFILE or manifest.get("selected_gene_ids") != GENES
            or manifest.get("is_fixture") is not False or set(manifest["files"]) != expected):
        raise ValueError("Snapshot scope/schema mismatch")
    if digest_manifest(manifest["files"]) != manifest["sha256"]:
        raise ValueError("Manifest checksum mismatch")
    payload = {}
    for name in sorted(expected):
        body = (root / "raw" / name).read_bytes()
        metadata = manifest["files"][name]
        if len(body) != metadata["bytes"] or hashlib.sha256(body).hexdigest() != metadata["sha256"]:
            raise ValueError(f"Raw checksum mismatch: {name}")
        payload[name] = json.loads(body)
    return manifest, payload
