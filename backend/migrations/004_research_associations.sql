-- Snapshot-scoped metadata prevents later imports from changing earlier results.
CREATE TABLE research_genes (
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 gene_id bigint NOT NULL REFERENCES genes(id),
 ensembl_id text NOT NULL CHECK (ensembl_id ~ '^ENSG[0-9]+$'),
 symbol text NOT NULL, name text NOT NULL,
 PRIMARY KEY(dataset_id,gene_id), UNIQUE(dataset_id,ensembl_id)
);
CREATE TABLE dataset_drugs (
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 drug_id text NOT NULL REFERENCES drugs(id), name text NOT NULL,
 drug_class text NOT NULL, maximum_stage text NOT NULL,
 PRIMARY KEY(dataset_id,drug_id)
);
CREATE TABLE dataset_pathways (
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 pathway_id text NOT NULL REFERENCES pathways(id), name text NOT NULL,
 PRIMARY KEY(dataset_id,pathway_id)
);
CREATE TABLE dataset_gene_pathways (
 dataset_id bigint NOT NULL, gene_id bigint NOT NULL, pathway_id text NOT NULL,
 PRIMARY KEY(dataset_id,gene_id,pathway_id),
 FOREIGN KEY(dataset_id,gene_id) REFERENCES research_genes(dataset_id,gene_id),
 FOREIGN KEY(dataset_id,pathway_id) REFERENCES dataset_pathways(dataset_id,pathway_id)
);
CREATE TABLE research_associations (
 dataset_id bigint NOT NULL, gene_id bigint NOT NULL, drug_id text NOT NULL,
 maximum_stage text NOT NULL, mechanisms jsonb NOT NULL CHECK(jsonb_typeof(mechanisms)='array'),
 PRIMARY KEY(dataset_id,gene_id,drug_id),
 FOREIGN KEY(dataset_id,gene_id) REFERENCES research_genes(dataset_id,gene_id),
 FOREIGN KEY(dataset_id,drug_id) REFERENCES dataset_drugs(dataset_id,drug_id)
);
CREATE TABLE research_diseases (
 dataset_id bigint NOT NULL, gene_id bigint NOT NULL, drug_id text NOT NULL,
 ontology_id text NOT NULL, name text NOT NULL,
 PRIMARY KEY(dataset_id,gene_id,drug_id,ontology_id),
 FOREIGN KEY(dataset_id,gene_id,drug_id) REFERENCES research_associations(dataset_id,gene_id,drug_id)
);
CREATE TABLE research_reports (
 dataset_id bigint NOT NULL, gene_id bigint NOT NULL, drug_id text NOT NULL,
 report_id text NOT NULL, source text NOT NULL, url text CHECK(url ~ '^https?://'),
 PRIMARY KEY(dataset_id,gene_id,drug_id,source,report_id),
 FOREIGN KEY(dataset_id,gene_id,drug_id) REFERENCES research_associations(dataset_id,gene_id,drug_id)
);
CREATE INDEX research_drug_lookup ON research_associations(dataset_id,drug_id);
