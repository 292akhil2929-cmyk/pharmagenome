# Scientific snapshot attribution

This directory contains real public-source data, not a development fixture.

Primary data: Lung Adenocarcinoma (TCGA, PanCancer Atlas), study luad_tcga_pan_can_atlas_2018, citation TCGA, Cell 2018, accessed through cBioPortal's documented public REST API. Only the ten selected genes listed in manifest.json were queried; all 566 mutation-profiled samples are retained.

cBioPortal documents its default data terms as the ODC Open Database License unless a study states otherwise. No additional restriction is stated in the captured public study metadata. Attribute both the original study and cBioPortal, preserve these notices, and observe the ODbL's applicable attribution/share-alike provisions when redistributing derived databases.
- https://docs.cbioportal.org/user-guide/faq/
- https://opendatacommons.org/licenses/odbl/1-0/
- https://gdc.cancer.gov/about-data/publications/pancanatlas
- Cerami et al., Cancer Discovery (2012), 2:401.
- Gao et al., Science Signaling (2013), 6:pl1.

Supporting coordinate-bound metadata: Ensembl GRCh37 REST /info/assembly/homo_sapiens, GRCh37.p13, GCA_000001405.14. Source URL, response hash and retrieval timestamp are in manifest.json. This supplies chromosome lengths, not reference allele validation.
- https://rest.ensembl.org/documentation/info/assembly_info

The repository's MIT license covers software only and does not relicense these scientific data. No controlled-access sequence files, imaging, survival outcomes or identifying clinical attributes were requested.
