"""Bounded, dataset-scoped descriptive genomics; no inference of clinical effect."""
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.db import connection

router = APIRouter(prefix="/api/genomics", tags=["Genomics"])
LIMIT = 50000
METHOD = "distinct-profiled-samples-v1"
LIMITATIONS = [
    "Descriptive frequencies in the selected imported cohort; not population prevalence.",
    "Only imported genes and variant types are represented. No reference-sequence callability is established.",
    "No observed matching variant does not establish wild-type status.",
    "Tumour VAF is sample read fraction, not population allele frequency.",
    "Chromosome counts are distinct variant identities, not length-normalized mutation density.",
    "Clinical significance, full gene names, pathways and drug associations are not supplied by this snapshot.",
]


def bounded(cursor):
    rows = cursor.fetchmany(LIMIT + 1)
    if len(rows) > LIMIT:
        raise HTTPException(503, "Dataset exceeds interactive limits; a batch analysis is required.")
    return rows


def read_data(dataset_id=None):
    with connection() as conn:
        dataset = conn.execute("""
            SELECT d.id,d.name,d.sha256,d.retrieved_at,d.is_fixture,d.manifest,
                   s.name AS source,s.url
            FROM dataset_versions d JOIN sources s ON s.id=d.source_id
            WHERE (%s::bigint IS NULL OR d.id=%s)
              AND EXISTS (SELECT 1 FROM ingestion_runs r WHERE r.dataset_id=d.id AND r.status='succeeded')
              AND EXISTS (SELECT 1 FROM molecular_profiles p WHERE p.dataset_id=d.id)
            ORDER BY d.retrieved_at DESC,d.id DESC LIMIT 1
        """, (dataset_id, dataset_id)).fetchone()
        if not dataset:
            raise HTTPException(404, "No completed genomic dataset found.")
        did = dataset["id"]
        members = bounded(conn.execute("""
            SELECT ps.profile_id,s.id AS sample_id,s.sample_identifier,
                   s.study_id,st.name AS study_name,d.id AS disease_id,d.name AS disease_name
            FROM molecular_profiles p JOIN profile_samples ps ON ps.profile_id=p.id
            JOIN samples s ON s.id=ps.sample_id JOIN studies st ON st.id=s.study_id
            JOIN diseases d ON d.id=s.disease_id
            WHERE p.dataset_id=%s ORDER BY s.sample_identifier,ps.profile_id
        """, (did,)))
        genes = bounded(conn.execute("""
            SELECT dg.gene_id AS id,dg.source_symbol AS symbol,dg.source_type AS gene_type,
                   pg.profile_id FROM dataset_genes dg JOIN profile_genes pg ON pg.gene_id=dg.gene_id
            JOIN molecular_profiles p ON p.id=pg.profile_id AND p.dataset_id=dg.dataset_id
            WHERE dg.dataset_id=%s ORDER BY dg.source_symbol,pg.profile_id
        """, (did,)))
        observations = bounded(conn.execute("""
            SELECT sv.sample_id,sv.profile_id,sv.variant_id,sv.variant_allele_fraction AS vaf,
                   v.assembly,v.chromosome,v.position,v.reference_allele AS ref,
                   v.alternate_allele AS alt,v.variant_type
            FROM sample_variants sv JOIN variants v ON v.id=sv.variant_id
            JOIN molecular_profiles p ON p.id=sv.profile_id AND p.dataset_id=sv.dataset_id
            WHERE sv.dataset_id=%s ORDER BY sv.variant_id,sv.sample_id,sv.profile_id
        """, (did,)))
        associations = bounded(conn.execute("""
            SELECT variant_id,gene_id,consequence FROM dataset_variant_genes
            WHERE dataset_id=%s ORDER BY variant_id,gene_id
        """, (did,)))
    return dataset, members, genes, observations, associations


def chromosome_key(value):
    return int(value) if value.isdigit() else {"X": 23, "Y": 24, "MT": 25}.get(value, 26)


def compute(members, genes, observations, associations, *, study="", disease="", gene="",
            chromosome="", variant_type="", q="", min_samples=0, page=1, page_size=25,
            sort="position", heatmap_page=1):
    """All denominators precede variant filters; count distinct sample identities."""
    cohort = {r["sample_id"]: r for r in members
              if (not study or r["study_id"] == study)
              and (not disease or str(r["disease_id"]) == disease)}
    profile_members = defaultdict(set)
    for row in members:
        if row["sample_id"] in cohort:
            profile_members[row["profile_id"]].add(row["sample_id"])
    gene_map = {}
    eligible = defaultdict(set)
    for row in genes:
        gene_map[row["id"]] = {"id": row["id"], "symbol": row["symbol"], "gene_type": row["gene_type"]}
        eligible[row["id"]].update(profile_members[row["profile_id"]])
    by_variant = defaultdict(list)
    for row in associations:
        if row["gene_id"] in gene_map:
            by_variant[row["variant_id"]].append(row)
    records = {}
    for row in observations:
        if row["sample_id"] not in profile_members[row["profile_id"]]:
            continue
        links = by_variant[row["variant_id"]]
        if gene and not any(gene_map[a["gene_id"]]["symbol"] == gene.upper() for a in links):
            continue
        if chromosome and row["chromosome"] != chromosome:
            continue
        if variant_type and row["variant_type"] != variant_type:
            continue
        locus = f'{row["chromosome"]}:{row["position"]}:{row["ref"]}>{row["alt"]}'
        symbols = [gene_map[a["gene_id"]]["symbol"] for a in links]
        if q and q.casefold() not in (" ".join(symbols) + " " + locus).casefold():
            continue
        key = (row["sample_id"], row["variant_id"])
        if key in records:
            # Do not silently select between discordant profile-level fractions.
            if records[key]["vaf"] != row["vaf"]:
                records[key] = {**records[key], "vaf": None}
        else:
            records[key] = row
    selected = list(records.values())
    variant_rows = {}
    mutated = defaultdict(set)
    gene_variants = defaultdict(set)
    gene_chromosomes = defaultdict(set)
    heat_cells = defaultdict(set)
    for row in selected:
        vid = row["variant_id"]
        links = by_variant[vid]
        for link in links:
            gid = link["gene_id"]
            if row["sample_id"] not in eligible[gid]:
                continue
            mutated[gid].add(row["sample_id"])
            gene_variants[gid].add(vid)
            gene_chromosomes[gid].add(row["chromosome"])
            heat_cells[gid].add(row["sample_id"])
        if vid not in variant_rows:
            variant_rows[vid] = {k: row[k] for k in
                                ("variant_id", "assembly", "chromosome", "position", "ref", "alt", "variant_type")}
            variant_rows[vid].update(genes=[gene_map[a["gene_id"]]["symbol"] for a in links],
                                     consequences=sorted({a["consequence"] for a in links if a["consequence"]}),
                                     samples=set(), vafs=[])
        variant_rows[vid]["samples"].add(row["sample_id"])
        if row["vaf"] is not None:
            variant_rows[vid]["vafs"].append(row["vaf"])
    variants = []
    for row in variant_rows.values():
        values = row.pop("vafs")
        variants.append({**row, "samples": len(row["samples"]),
                         "vaf_min": min(values) if values else None,
                         "vaf_max": max(values) if values else None,
                         "vaf_measured": len(values),
                         "clinical_significance": None, "population_allele_frequency": None})
    variants.sort(key=lambda r: (chromosome_key(r["chromosome"]), r["position"], r["ref"], r["alt"], r["variant_id"]))
    if sort == "samples":
        variants.sort(key=lambda r: -r["samples"])
    elif sort == "position_desc":
        variants.reverse()
    ranking = []
    for gid, row in gene_map.items():
        if gene and row["symbol"] != gene.upper():
            continue
        # Keep zero-frequency covered genes; search narrows names only when no matched loci exist.
        if q and q.casefold() not in row["symbol"].casefold() and not gene_variants[gid]:
            continue
        if len(mutated[gid]) < min_samples:
            continue
        n = len(eligible[gid])
        ranking.append({**row, "mutated_samples": len(mutated[gid]), "eligible_samples": n,
                        "frequency": len(mutated[gid]) / n if n else None,
                        "variants": len(gene_variants[gid]),
                        "observed_chromosomes": sorted(gene_chromosomes[gid], key=chromosome_key),
                        "gene_name": None, "gene_coordinates": None,
                        "pathways": None, "drug_targets": None})
    ranking.sort(key=lambda r: (-(r["frequency"] if r["frequency"] is not None else -1), r["symbol"]))
    bins = [{"label": f"{i * 10}–{(i + 1) * 10}%", "count": 0} for i in range(10)]
    missing = 0
    for row in selected:
        if row["vaf"] is None:
            missing += 1
        else:
            bins[min(int(row["vaf"] * 10), 9)]["count"] += 1
    chroms = Counter(row["chromosome"] for row in variants)
    types = Counter(row["variant_type"] for row in variants)
    sample_list = sorted(cohort.values(), key=lambda r: r["sample_identifier"])
    heat_total = len(sample_list)
    heat_page = min(heatmap_page, max(1, (heat_total + 39) // 40))
    sample_slice = sample_list[(heat_page - 1) * 40:heat_page * 40]
    actual_page = min(page, max(1, (len(variants) + page_size - 1) // page_size))
    return {
        "summary": {"eligible_samples": len(cohort), "mutated_samples": len({r["sample_id"] for r in selected}),
                    "variants": len(variants), "observations": len(selected),
                    "affected_genes": len([g for g in mutated if mutated[g]]), "missing_vaf": missing},
        "genes": ranking,
        "variants": {"items": variants[(actual_page - 1) * page_size:actual_page * page_size],
                     "total": len(variants), "page": actual_page, "page_size": page_size},
        "chromosomes": [{"label": c, "count": chroms[c]} for c in sorted(chroms, key=chromosome_key)],
        "variant_types": [{"label": t, "count": types[t]} for t in sorted(types)],
        "vaf_histogram": bins,
        "heatmap": {"page": heat_page, "page_size": 40, "total": heat_total,
                    "samples": [s["sample_identifier"] for s in sample_slice],
                    "rows": [{"symbol": g["symbol"],
                              "values": [1 if s["sample_id"] in heat_cells[g["id"]] else
                                         0 if s["sample_id"] in eligible[g["id"]] else None
                                         for s in sample_slice]} for g in ranking]},
    }


@router.get("")
def explore(dataset_id: int | None = Query(None, ge=1), study: str = Query("", max_length=150),
            disease: str = Query("", max_length=30), gene: str = Query("", max_length=80),
            chromosome: str = Query("", pattern=r"^([1-9]|1[0-9]|2[0-2]|X|Y|MT)?$"),
            variant_type: Literal["", "SNV", "MNV", "insertion", "deletion", "complex"] = "",
            q: str = Query("", max_length=80), min_samples: int = Query(0, ge=0, le=1000000),
            page: int = Query(1, ge=1, le=100000), page_size: int = Query(25, ge=1, le=100),
            sort: Literal["position", "position_desc", "samples"] = "position",
            heatmap_page: int = Query(1, ge=1, le=100000)):
    dataset, members, genes, observations, associations = read_data(dataset_id)
    filters = {"study": study, "disease": disease, "gene": gene, "chromosome": chromosome,
               "variant_type": variant_type, "q": q.strip(), "min_samples": min_samples,
               "page": page, "page_size": page_size, "sort": sort, "heatmap_page": heatmap_page}
    result = compute(members, genes, observations, associations, **filters)
    return {"dataset": dataset, "method": METHOD, "computed_at": datetime.now(UTC),
            "code_revision": os.getenv("VERCEL_GIT_COMMIT_SHA", "development"),
            "filters": {"dataset_id": dataset["id"], **filters},
            "limitations": LIMITATIONS, "options": {
                "studies": sorted({r["study_id"]: r["study_name"] for r in members}.items()),
                "diseases": sorted({str(r["disease_id"]): r["disease_name"] for r in members}.items()),
                "genes": sorted({r["symbol"] for r in genes}),
                "chromosomes": sorted({r["chromosome"] for r in observations}, key=chromosome_key),
                "variant_types": sorted({r["variant_type"] for r in observations}),
            }, **result}
