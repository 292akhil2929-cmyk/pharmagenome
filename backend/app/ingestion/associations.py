"""Pinned Open Targets research associations; no variant-response inference."""
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.ingestion.snapshot import digest_manifest

ROOT = Path(__file__).resolve().parents[2] / "data" / "research_associations"
API = "https://api.platform.opentargets.org/api/v4/graphql"
GENES = {"BRAF": 673, "EGFR": 1956, "KRAS": 3845, "MET": 4233, "NF1": 4763,
         "PIK3CA": 5290, "RB1": 5925, "STK11": 6794, "TP53": 7157, "KEAP1": 9817}
QUERY = """query($id: String!) { target(ensemblId:$id) {
 id approvedSymbol approvedName pathways { pathwayId pathway }
 drugAndClinicalCandidates { count rows { id maxClinicalStage
 drug { id name drugType maximumClinicalStage mechanismsOfAction {
 rows { mechanismOfAction actionType targets { id approvedSymbol } } } }
 diseases { disease { id name } } clinicalReports { id source url }
 } } } }"""
LIMITATIONS = [
    "Ten selected genes; a bounded source snapshot, not the complete drug or pathway universe.",
    "Drug links require a source mechanism that explicitly maps to the selected Ensembl target.",
    "Target mapping can include protein complexes; it does not establish selective binding or variant response.",
    "Disease labels and clinical report counts describe source-associated research, not approved indications.",
    "Maximum clinical stage is the source's historical drug-level label, not current regulatory advice.",
    "Pathway overlap counts selected genes; no enrichment, p-value, causal or treatment claim.",
    "Absence of a source link is not evidence that no biological relationship exists.",
    "No drug-response measurements or individual patient matching are included.",
]


def capture(root):
    root = Path(root)
    if root.exists():
        raise ValueError("Choose a new snapshot directory")
    (root / "raw").mkdir(parents=True)
    files = {}

    def fetch(name, url, query=None, variables=None):
        body_in = json.dumps({"query": query, "variables": variables}).encode() if query else None
        for attempt in range(3):
            try:
                req = Request(url, data=body_in, headers={"Content-Type": "application/json",
                              "Accept": "application/json", "User-Agent": "PharmaGenome/0.5"})
                with urlopen(req, timeout=60) as response:
                    body = response.read(20_000_001)
                if len(body) > 20_000_000:
                    raise ValueError("Snapshot response exceeds limit")
                obj = json.loads(body)
                if isinstance(obj, dict) and obj.get("errors"):
                    raise ValueError("GraphQL source returned errors")
                break
            except (HTTPError, URLError, TimeoutError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        (root / "raw" / name).write_bytes(body)
        files[name] = {"url": url, "query": query, "variables": variables,
                       "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
                       "retrieved_at": datetime.now(UTC).isoformat()}
        return obj

    for symbol in GENES:
        gene = fetch(f"gene-{symbol}.json",
                     f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{symbol}?content-type=application/json")
        if gene.get("display_name") != symbol or not re.fullmatch(r"ENSG[0-9]+", gene.get("id", "")):
            raise ValueError("Ensembl symbol mapping mismatch")
        fetch(f"target-{symbol}.json", API, QUERY, {"id": gene["id"]})
    manifest = {"schema_version": 1, "is_fixture": False, "genes": GENES,
                "retrieved_at": datetime.now(UTC).isoformat(), "files": files,
                "sha256": digest_manifest(files), "limitations": LIMITATIONS,
                "license": "Open Targets CC0 1.0; underlying source attribution retained.",
                "license_url": "https://platform-docs.opentargets.org/licence"}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return replay(root)


def replay(root=ROOT):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    expected = {f"{kind}-{symbol}.json" for kind in ["gene", "target"] for symbol in GENES}
    if (manifest.get("schema_version") != 1 or manifest.get("is_fixture") is not False
            or manifest.get("genes") != GENES or set(manifest["files"]) != expected
            or digest_manifest(manifest["files"]) != manifest["sha256"]):
        raise ValueError("Research snapshot scope or manifest checksum mismatch")
    payload = {}
    for name in expected:
        raw = (root / "raw" / name).read_bytes()
        meta = manifest["files"][name]
        if len(raw) != meta["bytes"] or hashlib.sha256(raw).hexdigest() != meta["sha256"]:
            raise ValueError("Research raw checksum mismatch: " + name)
        payload[name] = json.loads(raw)
    data = normalize(payload)
    (root / "quality-report.json").write_text(json.dumps(data["report"], indent=2) + "\n", encoding="utf-8")
    return manifest, data


def required(value, pattern=None):
    if not isinstance(value, str) or not value.strip() or (pattern and not re.fullmatch(pattern, value)):
        raise ValueError("Missing or invalid source identifier/text")
    return value.strip()


def safe_url(value):
    if value is None:
        return None
    return required(value, r"https://[^\s]+")


def normalize(payload):
    genes, drugs, pathways, memberships, associations = [], {}, {}, set(), {}
    report = {"downloaded": 0, "valid": 0, "invalid": 0, "excluded": 0, "duplicates": 0,
              "rejected_records": [], "unmapped_disease_labels": 0, "missing_report_urls": 0}
    for symbol, gene_id in GENES.items():
        mapping = payload[f"gene-{symbol}.json"]
        obj = payload[f"target-{symbol}.json"]
        target = obj.get("data", {}).get("target")
        if obj.get("errors") or not target:
            raise ValueError("Missing target or GraphQL errors")
        ensembl = required(mapping.get("id"), r"ENSG[0-9]+")
        if mapping.get("display_name") != symbol or target.get("id") != ensembl or target.get("approvedSymbol") != symbol:
            raise ValueError("Source gene identifier mismatch")
        genes.append({"id": gene_id, "symbol": symbol, "ensembl": ensembl,
                      "name": required(target.get("approvedName"))})
        for row in target["pathways"]:
            key = required(row.get("pathwayId"), r"R-HSA-[0-9]+")
            name = required(row.get("pathway"))
            if key in pathways and pathways[key] != name:
                raise ValueError("Conflicting pathway labels")
            pathways[key] = name
            memberships.add((gene_id, key))
        rows = target["drugAndClinicalCandidates"]
        if rows["count"] != len(rows["rows"]):
            raise ValueError("Truncated drug association response")
        for row in rows["rows"]:
            report["downloaded"] += 1
            try:
                drug = row.get("drug")
                if drug is None:
                    report["excluded"] += 1
                    report["rejected_records"].append({"gene": symbol, "id": row.get("id"), "reason": "No mapped drug"})
                    continue
                drug_id = required(drug.get("id"), r"[A-Za-z0-9_.:-]+")
                meta = {"id": drug_id, "name": required(drug.get("name")),
                        "drug_class": required(drug.get("drugType")),
                        "maximum_stage": required(drug.get("maximumClinicalStage"))}
                mechanisms = []
                for mechanism in (drug.get("mechanismsOfAction") or {}).get("rows", []):
                    targets = mechanism.get("targets") or []
                    if any(t["id"] == ensembl for t in targets):
                        mechanisms.append({"mechanism": required(mechanism.get("mechanismOfAction")),
                                           "action": required(mechanism.get("actionType")),
                                           "target_ids": sorted({required(t["id"], r"ENSG[0-9]+") for t in targets})})
                if not mechanisms:
                    report["excluded"] += 1
                    report["rejected_records"].append({"gene": symbol, "id": row.get("id"),
                                                       "reason": "No mechanism explicitly mapping this target"})
                    continue
                mechanisms = sorted({json.dumps(m, sort_keys=True) for m in mechanisms})
                diseases, reports = {}, {}
                for item in row["diseases"]:
                    disease = item.get("disease")
                    if disease is None:
                        report["unmapped_disease_labels"] += 1
                        continue
                    diseases[required(disease.get("id"), r"[A-Za-z0-9_:.-]+")] = required(disease.get("name"))
                for item in row["clinicalReports"]:
                    rid, source = required(item.get("id")), required(item.get("source"))
                    url = safe_url(item.get("url"))
                    if url is None:
                        report["missing_report_urls"] += 1
                    reports[(source, rid)] = {"id": rid, "source": source, "url": url}
                association = {"gene_id": gene_id, "drug_id": drug_id,
                               "maximum_stage": required(row.get("maxClinicalStage")),
                               "mechanisms": [json.loads(m) for m in mechanisms],
                               "diseases": [{"id": k, "name": v} for k, v in sorted(diseases.items())],
                               "reports": [v for _, v in sorted(reports.items())]}
                key = (gene_id, drug_id)
                if key in associations:
                    if associations[key] != association:
                        raise ValueError("Conflicting duplicate association")
                    report["duplicates"] += 1
                    continue
                if drug_id in drugs and drugs[drug_id] != meta:
                    raise ValueError("Conflicting drug metadata")
                drugs[drug_id], associations[key] = meta, association
                report["valid"] += 1
            except (ValueError, KeyError, TypeError) as exc:
                report["invalid"] += 1
                report["rejected_records"].append({"gene": symbol, "id": row.get("id"), "reason": str(exc)})
    report.update({"genes": len(genes), "drugs": len(drugs), "pathways": len(pathways),
                   "gene_pathway_memberships": len(memberships), "unit": "source drug-target candidate rows"})
    assert report["downloaded"] == sum(report[k] for k in ["valid", "invalid", "excluded", "duplicates"])
    return {"genes": genes, "drugs": list(drugs.values()), "pathways": pathways,
            "memberships": sorted(memberships), "associations": list(associations.values()), "report": report}
