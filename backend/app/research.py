"""Descriptive gene-drug and pathway associations from one immutable snapshot."""
import os
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.db import connection
from app.ingestion.associations import LIMITATIONS
from app.ingestion.load_associations import DATASET

router = APIRouter(prefix="/api/research", tags=["Research associations"])


def read_data(dataset_id=None):
    with connection() as conn:
        datasets = conn.execute("""SELECT d.id,d.name,d.sha256,d.retrieved_at,d.is_fixture,s.name AS source,s.url
                                FROM dataset_versions d JOIN sources s ON s.id=d.source_id
                                WHERE d.name=%s AND EXISTS
                                (SELECT 1 FROM ingestion_runs r WHERE r.dataset_id=d.id AND r.status='succeeded')
                                ORDER BY d.retrieved_at DESC,d.id DESC""", (DATASET,)).fetchall()
        dataset = next((d for d in datasets if dataset_id is None or d["id"] == dataset_id), None)
        if not dataset:
            raise HTTPException(404, "No completed research association snapshot found.")
        did = dataset["id"]
        genes = conn.execute("SELECT gene_id AS id,symbol,name,ensembl_id AS ensembl FROM research_genes WHERE dataset_id=%s",
                             (did,)).fetchall()
        drugs = conn.execute("SELECT drug_id AS id,name,drug_class,maximum_stage FROM dataset_drugs WHERE dataset_id=%s",
                             (did,)).fetchall()
        pathways = conn.execute("""SELECT p.pathway_id AS id,p.name,g.gene_id FROM dataset_pathways p
                                JOIN dataset_gene_pathways g USING(dataset_id,pathway_id)
                                WHERE p.dataset_id=%s""", (did,)).fetchall()
        associations = conn.execute("""SELECT gene_id,drug_id,maximum_stage,mechanisms
                                    FROM research_associations WHERE dataset_id=%s""", (did,)).fetchall()
        diseases = conn.execute("""SELECT gene_id,drug_id,ontology_id AS id,name
                                 FROM research_diseases WHERE dataset_id=%s""", (did,)).fetchall()
        reports = conn.execute("""SELECT gene_id,drug_id,report_id AS id,source,url
                                FROM research_reports WHERE dataset_id=%s""", (did,)).fetchall()
    for a in associations:
        a["diseases"] = [d for d in diseases if (d["gene_id"], d["drug_id"]) == (a["gene_id"], a["drug_id"])]
        a["reports"] = [r for r in reports if (r["gene_id"], r["drug_id"]) == (a["gene_id"], a["drug_id"])]
    return dataset, datasets, genes, drugs, pathways, associations


def compute(genes, drugs, pathways, associations, selected, q="", drug_class="", disease="", stage="",
            page=1, pathway_page=1, page_size=20, sort="name"):
    gene_map = {g["id"]: g for g in genes}
    selected_ids = {g["id"] for g in genes if g["symbol"] in selected}
    drug_map = {d["id"]: d for d in drugs}
    links = [a for a in associations if a["gene_id"] in selected_ids]
    if disease:
        links = [a for a in links if any(d["id"] == disease for d in a["diseases"])]
    matched = []
    for did in sorted({a["drug_id"] for a in links}):
        d = drug_map[did]
        if drug_class and d["drug_class"] != drug_class:
            continue
        if stage and d["maximum_stage"] != stage:
            continue
        if q.casefold() not in (d["name"] + " " + did).casefold():
            continue
        evidence = sorted([a for a in links if a["drug_id"] == did], key=lambda a: gene_map[a["gene_id"]]["symbol"])
        matched.append({**d, "url": "https://platform.opentargets.org/drug/" + did,
                        "targets": [gene_map[a["gene_id"]]["symbol"] for a in evidence],
                        "associations": [{**a, "symbol": gene_map[a["gene_id"]]["symbol"]} for a in evidence],
                        "report_count": len({(r["source"], r["id"]) for a in evidence for r in a["reports"]})})
    matched.sort(key=lambda d: (d["name"].casefold(), d["id"]))
    if sort == "reports":
        matched.sort(key=lambda d: -d["report_count"])
    # Pathways intentionally depend ONLY on the selected genes, not drug filters.
    grouped = {}
    for p in pathways:
        if p["gene_id"] not in selected_ids:
            continue
        item = grouped.setdefault(p["id"], {"id": p["id"], "name": p["name"], "genes": set()})
        item["genes"].add(gene_map[p["gene_id"]]["symbol"])
    ranked = [{**p, "genes": sorted(p["genes"]), "overlap": len(p["genes"]),
               "selected_gene_count": len(selected_ids),
               "url": "https://reactome.org/content/detail/" + p["id"]} for p in grouped.values()]
    ranked.sort(key=lambda p: (-p["overlap"], p["name"].casefold(), p["id"]))

    def paginate(rows, number):
        actual = min(number, max(1, (len(rows) + page_size - 1) // page_size))
        return {"items": rows[(actual - 1) * page_size:actual * page_size],
                "page": actual, "page_size": page_size, "total": len(rows)}
    return {"summary": {"selected_genes": len(selected_ids), "drugs": len(matched),
                         "target_links": sum(len(d["associations"]) for d in matched), "pathways": len(ranked)},
            "drugs": paginate(matched, page), "pathways": paginate(ranked, pathway_page),
            "selected_genes": sorted([g for g in genes if g["id"] in selected_ids], key=lambda g: g["symbol"])}


@router.get("")
def explore(dataset_id: int | None = Query(None, ge=1), genes: str = Query("", max_length=200),
            q: str = Query("", max_length=80), drug_class: str = Query("", max_length=80),
            disease: str = Query("", max_length=80), stage: str = Query("", max_length=80),
            page: int = Query(1, ge=1, le=100000), pathway_page: int = Query(1, ge=1, le=100000),
            page_size: int = Query(20, ge=1, le=100), sort: Literal["name", "reports"] = "name"):
    dataset, datasets, gene_rows, drugs, pathways, associations = read_data(dataset_id)
    selected = sorted({g.strip().upper() for g in genes.split(",") if g.strip()}) if genes else sorted(g["symbol"] for g in gene_rows)
    if set(selected) - {g["symbol"] for g in gene_rows}:
        raise HTTPException(422, "Selected genes must belong to this snapshot.")
    filters = {"genes": selected, "q": q.strip(), "drug_class": drug_class, "disease": disease,
               "stage": stage, "page": page, "pathway_page": pathway_page, "page_size": page_size, "sort": sort}
    return {"dataset": dataset, "datasets": datasets, "method": "Distinct source-linked drugs and selected-gene pathway overlap",
            "method_version": "1.0.0", "computed_at": datetime.now(UTC),
            "code_revision": os.getenv("VERCEL_GIT_COMMIT_SHA", "development"),
            "filters": {"dataset_id": dataset["id"], **filters}, "limitations": LIMITATIONS,
            "export_scope": "Current drug and pathway pages plus complete summary; page parameters are included.",
            "options": {"genes": sorted(gene_rows, key=lambda g: g["symbol"]),
                        "drug_classes": sorted({d["drug_class"] for d in drugs}),
                        "stages": sorted({d["maximum_stage"] for d in drugs}),
                        "diseases": sorted({d["id"]: d["name"] for a in associations for d in a["diseases"]}.items())},
            **compute(gene_rows, drugs, pathways, associations, selected, q.strip(), drug_class, disease,
                      stage, page, pathway_page, page_size, sort)}
