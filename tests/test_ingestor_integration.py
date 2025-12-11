import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from scripts.ingestion import GovInfoIngestor


class TestGetDocumentList:
    """Test suite for get_document_list method with nested path coverage."""

    @pytest.mark.asyncio
    async def test_get_document_list_xml_listing_nested_paths(self):
        """Test get_document_list handles XML listings with nested directories."""
        ingestor = GovInfoIngestor()
        
        # Mock XML response with nested structure
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <directory>
            <file>
                <name>test1.xml</name>
                <link>https://www.govinfo.gov/bulkdata/BILLS/118/test1.xml</link>
                <folder>false</folder>
            </file>
            <file>
                <name>subdir</name>
                <link>https://www.govinfo.gov/bulkdata/BILLS/118/subdir/</link>
                <folder>true</folder>
            </file>
            <file>
                <name>test2.xml</name>
                <link>https://www.govinfo.gov/bulkdata/BILLS/118/test2.xml</link>
                <folder>false</folder>
            </file>
        </directory>"""
        
        # Mock nested XML response
        nested_xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <directory>
            <file>
                <name>nested1.xml</name>
                <link>https://www.govinfo.gov/bulkdata/BILLS/118/subdir/nested1.xml</link>
                <folder>false</folder>
            </file>
            <file>
                <name>nested2.xml</name>
                <link>https://www.govinfo.gov/bulkdata/BILLS/118/subdir/nested2.xml</link>
                <folder>false</folder>
            </file>
        </directory>"""
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(side_effect=[xml_response, nested_xml_response])
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Test the method
        result = await ingestor.get_document_list(mock_session, 118, "BILLS")
        
        # Verify all XML files are found including nested ones
        expected_files = [
            "https://www.govinfo.gov/bulkdata/BILLS/118/test1.xml",
            "https://www.govinfo.gov/bulkdata/BILLS/118/test2.xml",
            "https://www.govinfo.gov/bulkdata/BILLS/118/subdir/nested1.xml",
            "https://www.govinfo.gov/bulkdata/BILLS/118/subdir/nested2.xml"
        ]
        
        assert len(result) == 4
        assert all(url in result for url in expected_files)

    @pytest.mark.asyncio
    async def test_get_document_list_json_fallback(self):
        """Test get_document_list falls back to JSON when XML fails."""
        ingestor = GovInfoIngestor()
        
        # Mock JSON response
        json_response = {
            "files": [
                {"name": "test1.xml", "link": "https://www.govinfo.gov/bulkdata/BILLS/118/test1.xml", "folder": False},
                {"name": "subdir", "link": "https://www.govinfo.gov/bulkdata/BILLS/118/subdir/", "folder": True},
                {"name": "test2.xml", "link": "https://www.govinfo.gov/bulkdata/BILLS/118/test2.xml", "folder": False}
            ]
        }
        
        mock_session = AsyncMock()
        
        # First call (XML) fails, second call (JSON) succeeds
        mock_xml_response = AsyncMock()
        mock_xml_response.status = 404
        
        mock_json_response = AsyncMock()
        mock_json_response.status = 200
        mock_json_response.json = AsyncMock(return_value=json_response)
        
        mock_session.get.return_value.__aenter__.side_effect = [mock_xml_response, mock_json_response]
        
        result = await ingestor.get_document_list(mock_session, 118, "BILLS")
        
        # Should find the XML files from JSON response
        assert len(result) >= 2
        assert any("test1.xml" in url for url in result)
        assert any("test2.xml" in url for url in result)

    @pytest.mark.asyncio
    async def test_get_document_list_error_handling(self):
        """Test get_document_list handles errors gracefully."""
        ingestor = GovInfoIngestor()
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        result = await ingestor.get_document_list(mock_session, 118, "BILLS")
        
        # Should return empty list on error
        assert result == []

    @pytest.mark.asyncio
    async def test_get_document_list_all_document_types(self):
        """Test get_document_list works with all supported document types."""
        ingestor = GovInfoIngestor()
        
        # Mock simple XML response for all types
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <directory>
            <file>
                <name>test.xml</name>
                <link>https://www.govinfo.gov/bulkdata/{}/118/test.xml</link>
                <folder>false</folder>
            </file>
        </directory>"""
        
        document_types = ["BILLS", "BILLSTATUS", "PLAW", "STATUTE", "FR", "CREC"]
        
        for doc_type in document_types:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=xml_response.format(doc_type))
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            result = await ingestor.get_document_list(mock_session, 118, doc_type)
            
            assert len(result) == 1
            assert doc_type in result[0]
            assert result[0].endswith(".xml")


@pytest.mark.asyncio
async def test_process_document_type_writes_manifest_and_failures(tmp_path: Path, monkeypatch):
    # Arrange
    ingestor = GovInfoIngestor(output_dir=tmp_path, workers=2, validate_xml=False)

    urls = [
        "https://example.com/ok.xml",
        "https://example.com/fail.xml",
    ]

    async def fake_get_document_list(self, session, congress, doc_type):
        return urls

    async def fake_download_file(self, session, url, output_path: Path, doc_type: str, retries: int = 0):
        if url.endswith("ok.xml"):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("<xml/>", encoding="utf-8")
            return True
        return False

    monkeypatch.setattr(GovInfoIngestor, "get_document_list", fake_get_document_list)
    monkeypatch.setattr(GovInfoIngestor, "download_file", fake_download_file)

    # Act
    async with aiohttp.ClientSession() as session:
        count = await ingestor.process_document_type(session, 118, "BILLS")

    # Assert download count
    assert count == 1

    # Assert manifest
    doc_dir = tmp_path / "118" / "BILLS"
    manifest_path = doc_dir / "manifest.json"
    failures_path = doc_dir / "failures.json"

    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["congress"] == 118
    assert manifest["doc_type"] == "BILLS"
    assert manifest["attempted"] == 2
    assert manifest["succeeded"] == 1
    assert manifest["failed"] == 1
    assert manifest["new_files_count"] == 1
    assert "ok.xml" in manifest["new_files"]

    # Assert failures
    assert failures_path.exists()
    failures = json.loads(failures_path.read_text())
    assert "failed_urls" in failures
    assert any(u.endswith("fail.xml") for u in failures["failed_urls"])