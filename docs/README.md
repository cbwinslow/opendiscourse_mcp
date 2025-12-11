# OpenDiscourse MCP - Documentation Reference

This folder contains comprehensive documentation and reference materials for building MCP servers to access bulk data from govinfo.gov and congress.gov.

## Repository Structure

### API Documentation
- **govinfo-api-summary.md** - Quick reference for GovInfo API
- **congress-api-summary.md** - Quick reference for Congress.gov API

### Downloaded Repositories
- **govinfo-api/** - Official GovInfo API repository with samples and documentation
- **govinfo-bulk-data/** - Bulk data repository with XML user guides
- **congress-api/** - Official Congress.gov API repository with client libraries
- **bill-status/** - Bill Status XML bulk data repository

### Key Resources

#### GovInfo.gov
- **API Base URL**: `https://api.govinfo.gov/`
- **Documentation**: `https://api.govinfo.gov/docs`
- **Bulk Data**: `https://www.govinfo.gov/bulkdata`
- **API Key**: Required from `https://api.data.gov/signup`

#### Congress.gov
- **API Base URL**: `https://api.congress.gov/v3/`
- **Documentation**: `https://api.congress.gov/`
- **API Key**: Required from `https://api.congress.gov/sign-up/`
- **Rate Limit**: 5,000 requests/hour

## Data Types Available

### GovInfo Collections
- Congressional Bills (BILLS)
- Congressional Record (CREC)
- Federal Register (FR)
- Code of Federal Regulations (CFR)
- U.S. Courts (USCOURTS)
- Committee Prints (CHRG)
- And many more...

### Congress.gov Data
- Bills and amendments
- Member information
- Committee data
- Nominations
- Roll call votes
- Hearing transcripts

## Next Steps for MCP Development

1. **Authentication Setup**
   - Obtain API keys for both services
   - Implement key management

2. **Server Architecture**
   - Design MCP server structure
   - Implement rate limiting
   - Add error handling

3. **Data Processing**
   - Parse XML/JSON responses
   - Implement data transformation
   - Add caching mechanisms

4. **Tool Implementation**
   - Create tools for common queries
   - Implement bulk download capabilities
   - Add search functionality