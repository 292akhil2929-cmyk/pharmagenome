"""Synthetic source-shaped records used only in isolated tests, never production."""
from app.ingestion.snapshot import GENES, PROFILE, STUDY


def fixture_payload():
    payload = {
        "study.json": {"studyId": STUDY, "publicStudy": True, "referenceGenome": "hg19",
                       "sequencedSampleCount": 2, "allSampleCount": 2, "name": "TEST FIXTURE",
                       "cancerTypeId": "luad", "cancerType": {"name": "TEST FIXTURE"}},
        "profile.json": {"molecularProfileId": PROFILE, "studyId": STUDY,
                         "molecularAlterationType": "MUTATION_EXTENDED"},
        "assembly.json": {"default_coord_system_version": "GRCh37", "top_level_region": [
            {"name": n, "length": 1000} for n in [str(i) for i in range(1, 23)] + ["X", "Y", "MT"]
        ]},
        "sample_ids.json": ["TEST-A", "TEST-B"],
        "samples.json": [{"sampleId": n, "patientId": n, "studyId": STUDY, "sequenced": True}
                         for n in ["TEST-A", "TEST-B"]],
    }
    for gene in GENES:
        payload[f"gene-{gene}.json"] = {"entrezGeneId": gene, "hugoGeneSymbol": f"TEST{gene}", "type": "test"}
        payload[f"mutations-{gene}.json"] = []
    payload["mutations-7157.json"] = [{
        "sampleId": "TEST-A", "studyId": STUDY, "molecularProfileId": PROFILE,
        "entrezGeneId": 7157, "chr": "17", "startPosition": 100, "endPosition": 100,
        "referenceAllele": "A", "variantAllele": "T", "variantType": "SNP", "ncbiBuild": "GRCh37",
        "mutationType": "TEST_CONSEQUENCE", "tumorAltCount": 3, "tumorRefCount": 9,
    }]
    return payload


def fixture_manifest():
    return {"sha256": "a" * 64, "study_id": STUDY, "profile_id": PROFILE,
            "selected_gene_ids": GENES, "retrieved_at": "2026-09-08T00:00:00+00:00",
            "license": "SYNTHETIC TEST FIXTURE", "is_fixture": True, "files": {}}
