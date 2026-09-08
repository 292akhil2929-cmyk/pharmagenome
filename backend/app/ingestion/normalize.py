"""Pure, deterministic normalization. Exclusions are not validation failures."""
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.ingestion.snapshot import GENES, PROFILE, STUDY


class Mutation(BaseModel):
    model_config = ConfigDict(strict=True)
    sampleId: str = Field(min_length=1)
    studyId: str
    molecularProfileId: str
    entrezGeneId: int = Field(gt=0)
    chr: str = Field(min_length=1)
    startPosition: int = Field(gt=0)
    endPosition: int = Field(gt=0)
    referenceAllele: str = Field(min_length=1, pattern=r"^[ACGTNacgtn-]+$")
    variantAllele: str = Field(min_length=1, pattern=r"^[ACGTNacgtn-]+$")
    variantType: str
    ncbiBuild: str
    mutationType: str
    tumorAltCount: int | None = Field(default=None, ge=-1)
    tumorRefCount: int | None = Field(default=None, ge=-1)


def normalize(payload):
    study, profile = payload["study.json"], payload["profile.json"]
    if study["studyId"] != STUDY or study.get("publicStudy") is not True:
        raise ValueError("Expected the public TCGA LUAD study")
    if study.get("referenceGenome") not in ("hg19", "GRCh37"):
        raise ValueError("Unsupported study assembly")
    if profile["molecularProfileId"] != PROFILE or profile["studyId"] != STUDY:
        raise ValueError("Profile/study mismatch")
    if profile["molecularAlterationType"] != "MUTATION_EXTENDED":
        raise ValueError("Expected mutation profile")
    assembly = payload["assembly.json"]
    if assembly["default_coord_system_version"] != "GRCh37":
        raise ValueError("Assembly metadata is not GRCh37")
    lengths = {x["name"]: x["length"] for x in assembly["top_level_region"]
               if x["name"] in [str(n) for n in range(1, 23)] + ["X", "Y", "MT"]}
    if len(lengths) != 25:
        raise ValueError("Incomplete chromosome length metadata")
    ids = payload["sample_ids.json"]
    if not ids or len(ids) != len(set(ids)) or len(ids) != study["sequencedSampleCount"]:
        raise ValueError("Incomplete or duplicated mutation-profile cohort")
    all_samples = payload["samples.json"]
    if len(all_samples) != study["allSampleCount"] or len({s["sampleId"] for s in all_samples}) != len(all_samples):
        raise ValueError("Incomplete or duplicated study sample metadata")
    samples = {s["sampleId"]: s for s in all_samples if s["sampleId"] in set(ids)}
    if set(samples) != set(ids) or any(s["studyId"] != STUDY for s in samples.values()):
        raise ValueError("Orphan or wrong-study cohort sample")
    if any(s.get("sequenced") is not True for s in samples.values()):
        raise ValueError("Cohort contains a sample not declared sequenced")
    genes = []
    for gene_id in GENES:
        gene = payload[f"gene-{gene_id}.json"]
        if gene["entrezGeneId"] != gene_id or not gene.get("hugoGeneSymbol"):
            raise ValueError("Missing gene identifier")
        genes.append({"id": gene_id, "symbol": gene["hugoGeneSymbol"].strip().upper(),
                      "type": gene.get("type")})
    if len({g["symbol"] for g in genes}) != len(GENES):
        raise ValueError("Conflicting gene symbols")
    observed, rejected, reasons, excluded_reasons = {}, [], Counter(), Counter()
    downloaded = invalid = excluded = duplicates = missing_vaf = 0
    for gene_id in GENES:
        source = f"mutations-{gene_id}.json"
        rows = payload[source]
        if not isinstance(rows, list):
            raise ValueError("Mutation response is not a list")
        for index, raw in enumerate(rows):
            downloaded += 1
            try:
                m = Mutation.model_validate(raw)
                chromosome = m.chr.removeprefix("chr").upper().replace("M", "MT") if m.chr == "M" else m.chr.removeprefix("chr").upper()
                if m.studyId != STUDY or m.molecularProfileId != PROFILE:
                    raise ValueError("wrong_study_or_profile")
                if m.entrezGeneId != gene_id or m.sampleId not in samples:
                    raise ValueError("orphan_gene_or_sample")
                if m.ncbiBuild not in ("GRCh37", "hg19", "37"):
                    raise ValueError("assembly_mismatch")
                if chromosome not in lengths or not 1 <= m.startPosition <= m.endPosition <= lengths[chromosome]:
                    raise ValueError("invalid_chromosomal_position")
                ref, alt = m.referenceAllele.upper(), m.variantAllele.upper()
                if ref == alt:
                    raise ValueError("identical_alleles")
                if m.variantType != "SNP" or len(ref) != 1 or len(alt) != 1:
                    excluded += 1
                    excluded_reasons["non_SNV"] += 1
                    rejected.append({"file": source, "row": index, "status": "excluded", "reason": "non_SNV"})
                    continue
                if ref not in "ACGT" or alt not in "ACGT":
                    excluded += 1
                    excluded_reasons["ambiguous_allele"] += 1
                    rejected.append({"file": source, "row": index, "status": "excluded", "reason": "ambiguous_allele"})
                    continue
                if m.startPosition != m.endPosition:
                    raise ValueError("SNV_coordinate_span")
                a, r = m.tumorAltCount, m.tumorRefCount
                vaf = a / (a + r) if a is not None and r is not None and min(a, r) >= 0 and a + r > 0 else None
                key = (m.sampleId, chromosome, m.startPosition, ref, alt)
                item = {"sample": m.sampleId, "chromosome": chromosome, "position": m.startPosition,
                        "ref": ref, "alt": alt, "vaf": vaf, "genes": {str(gene_id): m.mutationType}}
                if key in observed:
                    if observed[key]["vaf"] != vaf:
                        raise RuntimeError("Conflicting duplicate VAF values; snapshot must be reviewed")
                    observed[key]["genes"].update(item["genes"])
                    duplicates += 1
                else:
                    observed[key] = item
                    missing_vaf += vaf is None
            except (ValidationError, ValueError) as exc:
                invalid += 1
                reason = "schema_validation" if isinstance(exc, ValidationError) else str(exc)
                reasons[reason] += 1
                rejected.append({"file": source, "row": index, "status": "invalid", "reason": reason})
    observations = [observed[key] for key in sorted(observed)]
    variants = {(x["chromosome"], x["position"], x["ref"], x["alt"]) for x in observations}
    report = {"downloaded": downloaded, "valid": len(observations), "invalid": invalid,
              "excluded": excluded, "duplicates": duplicates, "unique_variants": len(variants),
              "samples": len(samples), "genes": len(genes), "missing_vaf": missing_vaf,
              "validation_reasons": dict(reasons), "exclusion_reasons": dict(excluded_reasons),
              "accepted_fraction": len(observations) / downloaded if downloaded else None,
              "method": "GRCh37 SNV import v1", "rejected_records": rejected,
              "coverage": "10 selected genes; unambiguous SNVs only; full mutation-profile cohort"}
    if downloaded != report["valid"] + invalid + excluded + duplicates:
        raise RuntimeError("Reconciliation failed")
    return {"study": study, "profile": profile, "genes": genes,
            "samples": [samples[key] for key in sorted(samples)], "observations": observations, "report": report}
