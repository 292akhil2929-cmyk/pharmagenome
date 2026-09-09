# PharmaGenome

<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
User brief: Next.js, TypeScript, shadcn/ui, Python FastAPI, PostgreSQL, Docker, GitHub Actions; Vercel deployment.

## Users
Researchers exploring genomic and pharmaceutical datasets; recruiters evaluating software, data science and bioinformatics skills.

## Product Purpose
Explore genomic variants, genes, diseases, pathways and drug-target research associations through reproducible computational analysis.

## Capabilities and Constraints
Build incrementally. Phase 1 establishes schema, API, frontend, Docker and tests. No scientific data or analytical results may be fabricated. Optional language-model explanation follows computation; it never replaces it. No diagnosis or treatment recommendations.

## Evidence on Hand
User's master build brief. The public TCGA LUAD ten-gene SNV snapshot is imported: 566 samples, 506 unique variants and 839 sample observations. Synthetic browser fixtures remain explicitly labeled.

## Brand Commitments
Professional scientific dashboard, clean typography, clear tables, subtle cards, responsive dark/light mode, restrained animation.

## Product Principles
Provenance is part of every result. Cohort denominators must be explicit. Computation works without LLMs. Scientific limitations remain visible.

## Open Decisions
Neon PostgreSQL is connected privately through Vercel. Through Phase 10, genomic explorers, sequence tools, drug/pathway research associations, statistical inference, CellMiner NCI-60 response modeling and the real-data analytical dashboard are implemented. Phase 8's evidence-constrained GPT-6 Astra integration and unavailable state remain implemented; live generation is gated on server-side OpenAI API access. External model validation and clinical use remain outside the delivered scope.
