# GovInfo API Documentation

## Overview
GovInfo API provides access to documents and metadata from all three branches of the Federal Government.

## Key Features
- Access to collections, packages, and granules
- Machine-readable JSON summaries
- Direct access to content files (PDF, HTM, XML)
- Metadata access (MODS, PREMIS)

## API Endpoints

### Collections Service
- Lists documents added or updated
- URL pattern: `https://api.govinfo.gov/collections/{collectionCode}/{date}?pageSize={size}&offsetMark={mark}&api_key={key}`

### Packages Service
- Package level summary information
- URL pattern: `https://api.govinfo.gov/packages/{packageId}/summary?api_key={key}`
- Content downloads: `/pdf`, `/htm`, `/xml`, `/zip`
- Metadata: `/mods`, `/premis`

### Granules Service
- Subsections of packages
- URL pattern: `https://api.govinfo.gov/packages/{packageId}/granules/{granuleId}/summary?api_key={key}`

## Authentication
- Requires API key from api.data.gov
- Demo key available: `DEMO_KEY`

## Rate Limits
- Check current documentation for limits

## Collections Available
- Congressional Bills (BILLS)
- Congressional Record (CREC)
- Federal Register (FR)
- Code of Federal Regulations (CFR)
- And many more...

## Bulk Data Repository
- XML data available at: https://www.govinfo.gov/bulkdata
- User guides available in docs/govinfo-bulk-data/