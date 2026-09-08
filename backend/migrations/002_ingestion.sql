ALTER TABLE ingestion_runs ADD COLUMN excluded bigint NOT NULL DEFAULT 0 CHECK(excluded >= 0);
ALTER TABLE ingestion_runs DROP CONSTRAINT ingestion_runs_check;
ALTER TABLE ingestion_runs ADD CONSTRAINT ingestion_reconciled CHECK (
 status <> 'succeeded' OR (
  finished_at IS NOT NULL AND downloaded = valid + invalid + duplicates + excluded
 )
);
ALTER TABLE dataset_versions ADD COLUMN manifest jsonb NOT NULL DEFAULT '{}';
ALTER TABLE genes ALTER COLUMN gene_name DROP NOT NULL;
CREATE TABLE dataset_genes (
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 gene_id bigint NOT NULL REFERENCES genes(id), source_symbol text NOT NULL, source_type text,
 PRIMARY KEY(dataset_id,gene_id)
);
CREATE TABLE study_dataset_versions (
 study_id text NOT NULL REFERENCES studies(id),
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 PRIMARY KEY(study_id,dataset_id)
);
CREATE INDEX ingestion_dataset_started_idx ON ingestion_runs(dataset_id,started_at DESC);
