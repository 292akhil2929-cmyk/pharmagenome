-- Coordinates are 1-based inclusive; assembly is part of variant identity.
CREATE TABLE sources (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 name text NOT NULL UNIQUE, url text NOT NULL CHECK (url ~ '^https://'),
 license text NOT NULL, access_notes text NOT NULL DEFAULT ''
);
CREATE TABLE dataset_versions (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 source_id bigint NOT NULL REFERENCES sources(id),
 name text NOT NULL, version text NOT NULL, retrieved_at timestamptz NOT NULL,
 sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
 is_fixture boolean NOT NULL DEFAULT false,
 UNIQUE(source_id,name,version)
);
CREATE TABLE ingestion_runs (
 id uuid PRIMARY KEY, dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 started_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz,
 status text NOT NULL CHECK (status IN ('running','succeeded','failed')),
 downloaded bigint NOT NULL DEFAULT 0 CHECK (downloaded >= 0),
 valid bigint NOT NULL DEFAULT 0 CHECK (valid >= 0),
 invalid bigint NOT NULL DEFAULT 0 CHECK (invalid >= 0),
 duplicates bigint NOT NULL DEFAULT 0 CHECK (duplicates >= 0),
 report jsonb NOT NULL DEFAULT '{}',
 CHECK (status <> 'succeeded' OR (finished_at IS NOT NULL AND downloaded = valid + invalid + duplicates))
);
CREATE TABLE genes (
 id bigint PRIMARY KEY CHECK (id > 0), gene_symbol text NOT NULL UNIQUE,
 gene_name text NOT NULL, description text NOT NULL DEFAULT ''
);
CREATE TABLE gene_locations (
 gene_id bigint NOT NULL REFERENCES genes(id), assembly text NOT NULL,
 chromosome text NOT NULL CHECK (chromosome ~ '^([1-9]|1[0-9]|2[0-2]|X|Y|MT)$'),
 start_position bigint NOT NULL CHECK (start_position > 0),
 end_position bigint NOT NULL, strand smallint NOT NULL CHECK (strand IN (-1,1)),
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 PRIMARY KEY(gene_id,assembly), CHECK(end_position >= start_position)
);
CREATE TABLE diseases (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, name text NOT NULL,
 ontology_id text NOT NULL UNIQUE, description text NOT NULL DEFAULT ''
);
CREATE TABLE studies (
 id text PRIMARY KEY, name text NOT NULL, dataset_id bigint NOT NULL REFERENCES dataset_versions(id)
);
CREATE TABLE samples (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 sample_identifier text NOT NULL, patient_identifier text,
 disease_id bigint NOT NULL REFERENCES diseases(id), study_id text NOT NULL REFERENCES studies(id),
 tissue text, population text, UNIQUE(study_id,sample_identifier)
);
CREATE TABLE molecular_profiles (
 id text PRIMARY KEY, study_id text NOT NULL REFERENCES studies(id),
 assay_type text NOT NULL, dataset_id bigint NOT NULL REFERENCES dataset_versions(id)
);
-- Membership is the denominator, including profiled samples with zero mutations.
CREATE TABLE profile_samples (
 profile_id text NOT NULL REFERENCES molecular_profiles(id),
 sample_id bigint NOT NULL REFERENCES samples(id), PRIMARY KEY(profile_id,sample_id)
);
CREATE TABLE profile_genes (
 profile_id text NOT NULL REFERENCES molecular_profiles(id),
 gene_id bigint NOT NULL REFERENCES genes(id), PRIMARY KEY(profile_id,gene_id)
);
CREATE TABLE variants (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, assembly text NOT NULL,
 chromosome text NOT NULL CHECK (chromosome ~ '^([1-9]|1[0-9]|2[0-2]|X|Y|MT)$'),
 position bigint NOT NULL CHECK (position > 0),
 reference_allele text NOT NULL CHECK (reference_allele ~ '^[ACGTN]+$'),
 alternate_allele text NOT NULL CHECK (alternate_allele ~ '^[ACGTN]+$'),
 variant_type text NOT NULL CHECK (variant_type IN ('SNV','MNV','insertion','deletion','complex')),
 CHECK(reference_allele <> alternate_allele),
 UNIQUE(assembly,chromosome,position,reference_allele,alternate_allele)
);
-- A locus may overlap more than one gene.
CREATE TABLE variant_genes (
 variant_id bigint NOT NULL REFERENCES variants(id), gene_id bigint NOT NULL REFERENCES genes(id),
 consequence text, PRIMARY KEY(variant_id,gene_id)
);
-- VAF is sample-specific; it is NOT a population allele frequency.
CREATE TABLE sample_variants (
 sample_id bigint NOT NULL, variant_id bigint NOT NULL REFERENCES variants(id),
 profile_id text NOT NULL, dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 variant_allele_fraction double precision CHECK (variant_allele_fraction BETWEEN 0 AND 1),
 quality double precision CHECK (quality >= 0 AND quality < 'Infinity'::float8),
 PRIMARY KEY(sample_id,variant_id,profile_id),
 FOREIGN KEY(profile_id,sample_id) REFERENCES profile_samples(profile_id,sample_id)
);
CREATE TABLE variant_annotations (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 variant_id bigint NOT NULL REFERENCES variants(id), dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 source_accession text NOT NULL, clinical_significance text, population text,
 population_allele_frequency double precision CHECK (population_allele_frequency BETWEEN 0 AND 1),
 UNIQUE(dataset_id,source_accession)
);
CREATE TABLE drugs (
 id text PRIMARY KEY, name text NOT NULL, drug_class text,
 mechanism text, approval_status text,
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id)
);
CREATE TABLE drug_targets (
 drug_id text NOT NULL REFERENCES drugs(id), gene_id bigint NOT NULL REFERENCES genes(id),
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id), target_type text NOT NULL,
 evidence_url text NOT NULL CHECK(evidence_url ~ '^https://'),
 PRIMARY KEY(drug_id,gene_id,dataset_id)
);
CREATE TABLE drug_diseases (
 drug_id text NOT NULL REFERENCES drugs(id), disease_id bigint NOT NULL REFERENCES diseases(id),
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id), relationship_type text NOT NULL,
 PRIMARY KEY(drug_id,disease_id,dataset_id)
);
CREATE TABLE pathways (
 id text PRIMARY KEY, pathway_name text NOT NULL, dataset_id bigint NOT NULL REFERENCES dataset_versions(id)
);
CREATE TABLE gene_pathways (
 gene_id bigint NOT NULL REFERENCES genes(id), pathway_id text NOT NULL REFERENCES pathways(id),
 PRIMARY KEY(gene_id,pathway_id)
);
CREATE TABLE drug_responses (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 sample_id bigint NOT NULL REFERENCES samples(id), drug_id text NOT NULL REFERENCES drugs(id),
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id), replicate text NOT NULL,
 response_value double precision NOT NULL CHECK(response_value > '-Infinity'::float8 AND response_value < 'Infinity'::float8),
 measurement_type text NOT NULL, unit text NOT NULL, response_category text,
 UNIQUE(sample_id,drug_id,dataset_id,measurement_type,replicate)
);
CREATE TABLE analysis_runs (
 id uuid PRIMARY KEY, created_at timestamptz NOT NULL DEFAULT now(),
 method text NOT NULL, method_version text NOT NULL, code_revision text NOT NULL,
 parameters jsonb NOT NULL, results jsonb NOT NULL,
 limitations jsonb NOT NULL DEFAULT '[]', random_seed integer
);
CREATE TABLE analysis_datasets (
 analysis_id uuid NOT NULL REFERENCES analysis_runs(id),
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id), PRIMARY KEY(analysis_id,dataset_id)
);
CREATE INDEX variants_locus_idx ON variants(assembly,chromosome,position);
CREATE INDEX variant_genes_gene_idx ON variant_genes(gene_id,variant_id);
CREATE INDEX samples_disease_study_idx ON samples(disease_id,study_id);
CREATE INDEX sample_variants_variant_idx ON sample_variants(variant_id,sample_id);
CREATE INDEX sample_variants_profile_idx ON sample_variants(profile_id,sample_id);
CREATE INDEX drug_targets_gene_idx ON drug_targets(gene_id);
CREATE INDEX gene_pathways_pathway_idx ON gene_pathways(pathway_id);
CREATE INDEX analyses_created_idx ON analysis_runs(created_at DESC);
