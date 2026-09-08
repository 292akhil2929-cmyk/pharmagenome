# Data sources

**Phase 1: no scientific datasets ingested.** Links below are planned adapters, not evidence of imported records. No sample counts, mutations, drugs or findings are invented.

| Source | URL | Planned dataset | Type / fields | Update frequency | License / access | Retrieved |
|---|---|---|---|---|---|---|
| cBioPortal | https://docs.cbioportal.org/web-api-and-clients/ | A bounded public lung-cancer cohort, to be selected | Study/profile IDs, profiled samples, mutation loci, Entrez genes, VAF if supplied | Source-dependent; capture a versioned snapshot | Check selected study's terms and consent/access restrictions before import | Not retrieved |
| NCBI Gene | https://www.ncbi.nlm.nih.gov/gene/ | Human gene metadata aligned to selected cohort | Gene ID, symbol, name, assembly and coordinates | Source-dependent | Record applicable NCBI data-use terms for the selected download | Not retrieved |
| ChEMBL | https://www.ebi.ac.uk/chembl/ | A bounded compound-target subset | ChEMBL IDs, target components, mechanism, evidence | Release-based; pin a release | Verify current license and attribution requirements before import | Not retrieved |
| Reactome | https://reactome.org/ | Human gene-pathway memberships | Stable pathway IDs, gene IDs, membership | Release-based; pin a release | Verify current license and attribution requirements before import | Not retrieved |

## Import contract
Download from official documented APIs/downloads. Preserve raw bytes with retrieval date and SHA-256. Validate before a transaction commits normalized rows. Record invalid and duplicate records. Never mix assemblies, VAF with population frequency, or variant rows with distinct sample counts. Use complete profiled cohort membership, including zero-mutation samples.

Fixture data must be explicitly marked in dataset_versions.is_fixture and prominently labeled in the interface. Tests use transient relational constraint records, never clinical evidence. Do not commit private data or credentials.

Drug-response and ML modules remain gated on a legally usable dataset, coherent response units, sufficient sample sizes and a defensible patient/study-aware split.
