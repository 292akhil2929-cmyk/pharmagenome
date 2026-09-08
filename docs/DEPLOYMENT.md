# Deployment verification notes

Deployments build directly from GitHub, with project roots frontend and backend. Credentials are stored by the Vercel Neon integration, not in this repository.

Next.js standalone output is enabled only for Docker/self-hosting. Vercel's Next 16.3 adapter has a documented standalone trace-file incompatibility: https://github.com/vercel/next.js/issues/96646 .

Neon's pooled connections reject statement_timeout in startup options. The API sets a transaction-local timeout after connecting. See https://neon.com/docs/connect/connection-errors .

The initial schema migration runs in the trusted backend build, never in an HTTP endpoint. The same build imports the pinned public TCGA LUAD snapshot atomically. Repeat deployments are no-ops for an already imported checksum. Database readiness must return 200 and schema_version 003_genomics after deploy.
