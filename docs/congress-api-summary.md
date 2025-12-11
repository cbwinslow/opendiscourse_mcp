# Congress.gov API Documentation

## Overview
Congress.gov API provides machine-readable data from collections available on Congress.gov.

## Key Features
- Access to bills, amendments, members, committees, nominations
- XML and JSON response formats
- Comprehensive legislative data

## API Endpoints

### Base URL
`https://api.congress.gov/v3/`

### Main Endpoints
- **Bills**: `/bill/{congress}/{chamber}/{billNumber}`
- **Amendments**: `/amendment/{congress}/{chamber}/{billNumber}/{amendmentNumber}`
- **Members**: `/member`
- **Committees**: `/committee`
- **Nominations**: `/nomination`
- **Committee Meetings**: `/committee-meeting`
- **Hearings**: `/hearing`
- **Reports**: `/committee-report`

## Authentication
- Requires API key from https://api.congress.gov/sign-up/
- Rate limit: 5,000 requests per hour
- Default: 20 results, max: 250 results

## Response Structure
Every response contains:
- **Request**: API request information
- **Pagination**: Count, next/previous page URLs
- **Data**: Main data (name varies by endpoint)

## Coverage
- Coverage dates available at: https://www.congress.gov/help/coverage-dates
- Estimated update times provided

## Client Libraries
- Java client available in docs/congress-api/java/
- Python client available in docs/congress-api/python/
- Sample outputs provided

## Version
- Current version: v3
- ChangeLog available in docs/congress-api/ChangeLog.md