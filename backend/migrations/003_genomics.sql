-- Preserve gene/consequence associations in the same snapshot as observations.
CREATE TABLE dataset_variant_genes (
 dataset_id bigint NOT NULL REFERENCES dataset_versions(id),
 variant_id bigint NOT NULL REFERENCES variants(id),
 gene_id bigint NOT NULL REFERENCES genes(id),
 consequence text,
 PRIMARY KEY(dataset_id,variant_id,gene_id)
);
-- Existing Phase 2 snapshots used the shared association table.
INSERT INTO dataset_variant_genes(dataset_id,variant_id,gene_id,consequence)
SELECT DISTINCT sv.dataset_id,vg.variant_id,vg.gene_id,vg.consequence
FROM sample_variants sv JOIN variant_genes vg ON vg.variant_id=sv.variant_id
JOIN dataset_genes dg ON dg.dataset_id=sv.dataset_id AND dg.gene_id=vg.gene_id;
CREATE INDEX dataset_variant_gene_lookup ON dataset_variant_genes(dataset_id,gene_id,variant_id);
CREATE INDEX observations_dataset_lookup ON sample_variants(dataset_id,variant_id,sample_id);
