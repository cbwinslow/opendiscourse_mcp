# GovInfo Bulk Data Download Process

## Overview

This document describes the bulk data download process for the GovInfo.gov MCP Server. The process involves downloading XML files and XSL schemas from the [govinfo.gov bulk data repository](https://www.govinfo.gov/bulkdata).

## API Structure

### Base URL
```
https://www.govinfo.gov/bulkdata/
```

### Collection Structure
The bulk data is organized in a hierarchical structure:

```
bulkdata/
├── BILLS/                  # Bills collection
│   ├── 119/               # 119th Congress
│   │   ├── 1/             # 1st Session
│   │   │   ├── hr/        # House bills
│   │   │   │   ├── BILLS-119hr23ih.xml  # Individual bill XML
│   │   │   │   ├── BILLS-119hr29ih.xml
│   │   │   │   └── ...
│   │   │   ├── s/         # Senate bills
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── FR/                    # Federal Register
├── CFR/                   # Code of Federal Regulations
├── CONGREC/               # Congressional Record
└── ...                    # Other collections
```

### API Endpoints

1. **XML Listing Endpoint**: Returns directory listing in XML format
   ```
   https://www.govinfo.gov/bulkdata/xml/{collection}/{path}
   ```

2. **JSON Listing Endpoint**: Returns directory listing in JSON format
   ```
   https://www.govinfo.gov/bulkdata/json/{collection}/{path}
   ```

3. **Direct File Download**: Download individual files
   ```
   https://www.govinfo.gov/bulkdata/{collection}/{path}/{filename}
   ```

## Download Process

### 1. Collection Discovery

The downloader first discovers available collections by:
- Using a predefined list of common collections
- Optionally fetching from the root API endpoint

### 2. Directory Traversal

For each collection, the downloader traverses the directory structure:
1. **Collection Level**: `https://www.govinfo.gov/bulkdata/xml/BILLS`
2. **Congress Level**: `https://www.govinfo.gov/bulkdata/xml/BILLS/119`
3. **Session Level**: `https://www.govinfo.gov/bulkdata/xml/BILLS/119/1`
4. **Bill Type Level**: `https://www.govinfo.gov/bulkdata/xml/BILLS/119/1/hr`
5. **File Level**: Individual XML files

### 3. File Identification

The downloader identifies downloadable files by:
- Checking for `<folder>false</folder>` in XML responses
- Filtering by file extensions (`.xml`, `.xsl`, `.xsd`)
- Extracting file URLs from `<link>` elements

### 4. Concurrent Download

Files are downloaded concurrently using a thread pool:
- Configurable number of workers (default: 15)
- Automatic retry for failed downloads
- Progress tracking and logging

### 5. Duplication Prevention

To prevent duplicate downloads:
- Maintains a tracking file with downloaded URLs
- Uses file checksums for verification
- Skips already downloaded files

## Implementation Details

### Python Implementation

The download process is orchestrated by `scripts/ingest_govinfo.py` (CLI) built on `scripts/ingestion/ingestor.py`.

Example (programmatic):

```python
import asyncio
from pathlib import Path
from scripts.ingestion import ingest_congress_data

# Download BILLS and BILLSTATUS for the 118th Congress to govinfo_data/
result = asyncio.run(
    ingest_congress_data(congress=118, doc_types=["BILLS", "BILLSTATUS"], output_dir=Path("govinfo_data"))
)
print(result)
```

### Command Line Usage

```bash
# Single congress, default document types (113–119 supported by default config)
python3 scripts/ingest_govinfo.py --congress 118

# Multiple congresses and selected document types
python3 scripts/ingest_govinfo.py --congress 117 118 --doc-types BILLS BILLSTATUS

# All configured congresses
python3 scripts/ingest_govinfo.py --all

# Change workers and output directory
python3 scripts/ingest_govinfo.py --congress 118 --workers 8 --output govinfo_data
```

Note: The legacy standalone downloader scripts are deprecated in favor of the async ingestion CLI shown above.

## Configuration

### Settings

The downloader uses the following configurable settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `max_concurrent_requests` | 15 | Maximum concurrent downloads |
| `request_timeout` | 60 | Request timeout in seconds |
| `retry_delay` | 2 | Initial retry delay in seconds |
| `max_retries` | 3 | Maximum retry attempts |
| `data_directory` | `data/govinfo` | Base download directory |

### Environment Variables

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- Custom settings can be added as needed

## Error Handling

### Common Errors

1. **HTTP 406**: Accept header mismatch
   - Solution: Use wildcard accept header (`*/*`)

2. **HTTP 429**: Rate limiting
   - Solution: Implement exponential backoff

3. **Connection Errors**: Network issues
   - Solution: Automatic retry with increasing delays

4. **File Not Found**: Missing files
   - Solution: Skip and log missing files

### Error Recovery

- Automatic retry for transient errors
- Skip permanently failed files
- Continue with remaining files
- Detailed error logging

## Data Validation

### File Verification

1. **Checksum Verification**: SHA256 checksums for downloaded files
2. **Size Verification**: Compare downloaded size with expected size
3. **XML Validation**: Validate XML structure (future enhancement)

### Duplicate Detection

1. **URL Tracking**: Maintain list of downloaded URLs
2. **Checksum Comparison**: Detect duplicate content
3. **File Size Comparison**: Additional verification

## Performance Optimization

### Concurrent Processing

- Thread pool for parallel downloads
- Configurable worker count
- Batch processing of files

### Memory Management

- Streamed file downloads
- Efficient memory usage
- Progress tracking

### Network Efficiency

- Connection reuse
- Proper HTTP headers
- Rate limiting compliance

## Monitoring and Logging

### Logging Levels

- **DEBUG**: Detailed debugging information
- **INFO**: Normal operation messages
- **WARNING**: Potential issues
- **ERROR**: Serious problems

### Log Files

- Console output
- File logging to `logs/govinfo_downloader_standalone.log`
- Progress tracking files

## Example Workflow

### Example Workflow

```bash
# Create output directory (optional)
mkdir -p govinfo_data

# Download BILLS and BILLSTATUS for the 118th Congress
python3 scripts/ingest_govinfo.py --congress 118 --doc-types BILLS BILLSTATUS --workers 8 --output govinfo_data
```

### Expected Output

```
2025-12-11 10:00:00 - INFO - Starting download for collection: BILLS
2025-12-11 10:00:00 - INFO - Base directory: data/govinfo
2025-12-11 10:00:00 - INFO - Max workers: 10
2025-12-11 10:00:00 - INFO - Fetching file list for BILLS...
2025-12-11 10:00:05 - INFO - Found 1250 files to download
2025-12-11 10:00:05 - INFO - ✅ Downloaded https://www.govinfo.gov/bulkdata/BILLS/119/1/hr/BILLS-119hr23ih.xml (22270 bytes, 1.23s)
2025-12-11 10:00:05 - INFO - ✅ Downloaded https://www.govinfo.gov/bulkdata/BILLS/119/1/hr/BILLS-119hr29ih.xml (17268 bytes, 0.87s)
...

============================================================
GOVINFO BULK DOWNLOAD SUMMARY
============================================================
Total Files Processed: 1250
Successful Downloads: 1245
Failed Downloads: 5
Skipped Files: 0
Total Data Downloaded: 125.45 MB
Duration: 120.45 seconds
Average Speed: 1.04 MB/s
Start Time: 2025-12-11 10:00:00
End Time: 2025-12-11 10:02:00
============================================================
```

## File Structure

### Downloaded Files

```
data/govinfo/
├── BILLS/
│   ├── 119/
│   │   ├── 1/
│   │   │   ├── hr/
│   │   │   │   ├── BILLS-119hr23ih.xml
│   │   │   │   ├── BILLS-119hr29ih.xml
│   │   │   │   └── ...
│   │   │   ├── s/
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── FR/
├── CFR/
└── ...
```

### Tracking Files and Artifacts

```
govinfo_data/
└── {congress}/
    └── {doc_type}/
        ├── manifest.json          # Run summary and file inventory
        └── failures.json          # Failed URLs from the last run (if any)
```

Notes:
- Re-running the same command skips already-downloaded files and updates manifest.json accordingly.
- failures.json is only present when failures occur.

## Best Practices

### Download Strategy

1. **Start Small**: Test with a single collection first
2. **Limit Workers**: Start with fewer workers, increase as needed
3. **Monitor Progress**: Check logs and progress files
4. **Resume Capability**: Use `--resume` for interrupted downloads

### Storage Management

1. **Disk Space**: Ensure sufficient disk space
2. **Directory Structure**: Maintain original structure
3. **File Organization**: Keep related files together

### Error Handling

1. **Review Logs**: Check for failed downloads
2. **Retry Failed**: Manually retry failed files if needed
3. **Report Issues**: Document persistent issues

## Future Enhancements

### Planned Features

1. **Incremental Updates**: Download only new/changed files
2. **Metadata Extraction**: Extract metadata from XML files
3. **Database Integration**: Store downloaded data in database
4. **Validation**: XML schema validation
5. **Compression**: Support for ZIP archives

### Performance Improvements

1. **Batch Processing**: Process files in batches
2. **Memory Optimization**: Better memory management
3. **Network Optimization**: Improved HTTP handling

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Slow downloads | Reduce worker count, check network |
| Failed downloads | Check API status, retry later |
| Disk space issues | Clean up old files, increase space |
| Permission errors | Check directory permissions |
| Rate limiting | Reduce concurrency, add delays |

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
python3 scripts/ingest_govinfo.py --congress 118 --doc-types BILLS --workers 5
```

## Conclusion

The GovInfo bulk download process provides a robust solution for downloading government data in bulk. With concurrent processing, error handling, and duplication prevention, it efficiently handles large datasets while maintaining data integrity.

For production use, consider:
- Running during off-peak hours
- Monitoring disk space usage
- Implementing proper error monitoring
- Regularly updating to latest data