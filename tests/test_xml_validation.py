"""Tests for the XML validator module."""

from pathlib import Path
from unittest.mock import AsyncMock

import aiohttp
import pytest

from scripts.ingestion.xml_validator import XMLValidator


@pytest.fixture
def sample_bill_xml() -> str:
    """Return a sample bill XML string."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<bill xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BILLS-118.xsd">
    <billNumber>1</billNumber>
    <title>Test Bill</title>
    <congress>118</congress>
    <type>hr</type>
</bill>"""


@pytest.fixture
def sample_invalid_xml() -> str:
    """Return an invalid XML string."""
    return """<?xml version="1.0"?>
<bill>
    <invalid>This is not valid</invalid>
</bill>"""


@pytest.fixture
def sample_malformed_xml() -> str:
    """Return a malformed XML string."""
    return """<?xml version="1.0"?>
<bill>
    <unclosed_tag>
</bill>"""


@pytest.fixture
def sample_xsd_schema() -> str:
    """Return a sample XSD schema."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="bill">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="billNumber" type="xs:integer"/>
                <xs:element name="title" type="xs:string"/>
                <xs:element name="congress" type="xs:integer"/>
                <xs:element name="type" type="xs:string"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>"""


class TestXMLValidator:
    """Test suite for the XMLValidator class."""

    def test_xml_validator_init_with_default_schema_dir(self):
        """Test XMLValidator initialization with default schema directory."""
        validator = XMLValidator()
        assert validator.schema_dir.endswith("schemas")
        assert isinstance(validator.schemas, dict)

    def test_xml_validator_init_with_custom_schema_dir(self, tmp_path):
        """Test XMLValidator initialization with custom schema directory."""
        custom_dir = str(tmp_path / "custom_schemas")
        validator = XMLValidator(custom_dir)
        assert validator.schema_dir == custom_dir
        assert Path(custom_dir).exists()

    def test_xml_validator_loads_schemas_from_directory(
        self, tmp_path, sample_xsd_schema
    ):
        """Test XMLValidator loads schemas from directory."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        (schema_dir / "bill.xsd").write_text(sample_xsd_schema)

        validator = XMLValidator(str(schema_dir))
        assert "bill" in validator.schemas
        assert validator.schemas["bill"] is not None

    def test_xml_validator_validate_xml_success(
        self, sample_bill_xml, sample_xsd_schema, tmp_path
    ):
        """Test XMLValidator successfully validates valid XML."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        (schema_dir / "bill.xsd").write_text(sample_xsd_schema)

        validator = XMLValidator(str(schema_dir))
        is_valid, errors = validator.validate_xml(sample_bill_xml, "bill")

        assert is_valid is True
        assert errors == []

    def test_xml_validator_validate_xml_invalid_structure(
        self, sample_invalid_xml, sample_xsd_schema, tmp_path
    ):
        """Test XMLValidator rejects XML with invalid structure."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        (schema_dir / "bill.xsd").write_text(sample_xsd_schema)

        validator = XMLValidator(str(schema_dir))
        is_valid, errors = validator.validate_xml(sample_invalid_xml, "bill")

        assert is_valid is False
        assert len(errors) > 0
        assert any("not expected" in error for error in errors)

    def test_xml_validator_validate_xml_malformed(
        self, sample_malformed_xml, sample_xsd_schema, tmp_path
    ):
        """Test XMLValidator handles malformed XML gracefully."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        (schema_dir / "bill.xsd").write_text(sample_xsd_schema)

        validator = XMLValidator(str(schema_dir))
        is_valid, errors = validator.validate_xml(sample_malformed_xml, "bill")

        assert is_valid is False
        assert len(errors) > 0
        assert any("XML syntax error" in error for error in errors)

    def test_xml_validator_validate_xml_schema_not_found(self, sample_bill_xml):
        """Test XMLValidator handles missing schema gracefully."""
        validator = XMLValidator()
        is_valid, errors = validator.validate_xml(sample_bill_xml, "nonexistent")

        assert is_valid is False
        assert "Schema nonexistent not found" in errors

    @pytest.mark.asyncio
    async def test_download_schema_success(self, sample_xsd_schema, tmp_path):
        """Test successful schema download."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Mock aiohttp session and response
        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=sample_xsd_schema)
        mock_session.get.return_value.__aenter__.return_value = mock_response

        validator = XMLValidator(str(schema_dir))
        result = await validator.download_schema(
            mock_session, "http://example.com/schema.xsd", "test"
        )

        assert result is True
        assert (schema_dir / "test.xsd").exists()
        assert (schema_dir / "test.xsd").read_text() == sample_xsd_schema
        assert "test" in validator.schemas

    @pytest.mark.asyncio
    async def test_download_schema_http_error(self, tmp_path):
        """Test schema download with HTTP error."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Mock aiohttp session and response with error
        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_session.get.return_value.__aenter__.return_value = mock_response

        validator = XMLValidator(str(schema_dir))
        result = await validator.download_schema(
            mock_session, "http://example.com/schema.xsd", "test"
        )

        assert result is False
        assert not (schema_dir / "test.xsd").exists()

    @pytest.mark.asyncio
    async def test_download_schema_exception(self, tmp_path):
        """Test schema download with exception."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Mock aiohttp session that raises exception
        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.get.side_effect = aiohttp.ClientError("Network error")

        validator = XMLValidator(str(schema_dir))
        result = await validator.download_schema(
            mock_session, "http://example.com/schema.xsd", "test"
        )

        assert result is False
        assert not (schema_dir / "test.xsd").exists()

    def test_schema_directory_creation(self, tmp_path):
        """Test that schema directory is created if it doesn't exist."""
        schema_dir = tmp_path / "new_schemas"
        assert not schema_dir.exists()

        XMLValidator(str(schema_dir))
        assert schema_dir.exists()
        assert schema_dir.is_dir()

    def test_load_schemas_ignores_non_xsd_files(self, tmp_path, sample_xsd_schema):
        """Test that non-XSD files are ignored when loading schemas."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        (schema_dir / "bill.xsd").write_text(sample_xsd_schema)
        (schema_dir / "readme.txt").write_text("This is not a schema")
        (schema_dir / "config.json").write_text("{}")

        validator = XMLValidator(str(schema_dir))
        assert "bill" in validator.schemas
        assert "readme" not in validator.schemas
        assert "config" not in validator.schemas

    def test_load_schemas_handles_invalid_xsd(self, tmp_path, sample_xsd_schema):
        """Test that invalid XSD files are handled gracefully."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        (schema_dir / "valid.xsd").write_text(sample_xsd_schema)
        (schema_dir / "invalid.xsd").write_text("This is not valid XSD")

        validator = XMLValidator(str(schema_dir))
        # Valid schema should be loaded
        assert "valid" in validator.schemas
        # Invalid schema should be ignored (no exception raised)
        assert "invalid" not in validator.schemas
