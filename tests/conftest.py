"""Pytest configuration and fixtures for the test suite."""
import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
import pytest
import aiohttp
from aiohttp import web
from aioresponses import aioresponses

# Add the project root to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "fixtures"

# Sample XML content for testing
SAMPLE_BILL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<bill>
    <billNumber>1</billNumber>
    <title>Test Bill</title>
    <congress>117</congress>
    <type>hr</type>
</bill>
"""

SAMPLE_BILLSTATUS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<billStatus>
    <bill>
        <billNumber>1</billNumber>
        <title>Test Bill Status</title>
        <congress>117</congress>
        <type>hr</type>
        <actions>
            <item>
                <actionDate>2023-01-01</actionDate>
                <text>Introduced in House</text>
            </item>
        </actions>
    </bill>
</billStatus>
"""

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_aioresponse():
    """Fixture for mocking aiohttp responses."""
    with aioresponses() as m:
        yield m

@pytest.fixture
def test_app():
    """Create a test aiohttp application."""
    app = web.Application()
    return app

@pytest.fixture
async def test_client(aiohttp_client, test_app):
    """Create a test client for aiohttp applications."""
    return await aiohttp_client(test_app)

@pytest.fixture
def mock_govinfo_server() -> Dict[str, Any]:
    """Create a mock govinfo server with test data."""
    return {
        "base_url": "https://www.govinfo.gov/bulkdata",
        "bills": {
            "117/BILLS/117hr1ih.xml": SAMPLE_BILL_XML,
            "117/BILLSTATUS/117hr1.xml": SAMPLE_BILLSTATUS_XML,
        },
        "sitemap": """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex>
            <sitemap>
                <loc>https://www.govinfo.gov/bulkdata/BILLS/117/BILLS-117hr1ih.xml</loc>
            </sitemap>
        </sitemapindex>
        """
    }

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir

@pytest.fixture
def test_config(temp_output_dir):
    """Create a test configuration."""
    return {
        "output_dir": temp_output_dir,
        "workers": 2,
        "rate_limit": 10,
        "chunk_size": 1024,
        "validate_xml": True,
        "timeout": 30,
        "max_retries": 3,
    }
