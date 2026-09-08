CREATE TABLE cell_line_features (
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 sample_id bigint NOT NULL REFERENCES samples(id),
 gene_id bigint NOT NULL REFERENCES genes(id),
 feature_type text NOT NULL CHECK(feature_type IN ('expression_z_score','protein_affecting_mutation')),
 feature_value double precision NOT NULL CHECK(feature_value > '-Infinity'::float8 AND feature_value < 'Infinity'::float8),
 unit text NOT NULL,
 PRIMARY KEY(dataset_id,sample_id,gene_id,feature_type)
);
CREATE INDEX cell_line_features_lookup ON cell_line_features(dataset_id,feature_type,gene_id,sample_id);
CREATE INDEX drug_responses_lookup ON drug_responses(dataset_id,drug_id,sample_id);
