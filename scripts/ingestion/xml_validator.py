"""XML validation utilities for govinfo.gov data."""
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
from lxml import etree as etree
from lxml.etree import XMLSyntaxError
import xmlschema

logger = logging.getLogger(__name__)

class XMLValidator:
    """Handles XML schema validation for govinfo.gov data."""
    
    def __init__(self, schema_dir: Optional[str] = None):
        """
        Initialize the XML validator.
        
        Args:
            schema_dir: Directory containing XSD schemas. Defaults to 'schemas' in the same directory.
        """
        self.schema_dir = schema_dir or os.path.join(os.path.dirname(__file__), 'schemas')
        self.schemas: Dict[str, xmlschema.XMLSchema] = {}
        self._load_schemas()
    
    def _load_schemas(self) -> None:
        """Load all XSD schemas from the schemas directory."""
        schema_dir = Path(self.schema_dir)
        if not schema_dir.exists():
            schema_dir.mkdir(parents=True, exist_ok=True)
            return
            
        for schema_file in schema_dir.glob('*.xsd'):
            try:
                schema = xmlschema.XMLSchema(str(schema_file))
                self.schemas[schema_file.stem] = schema
            except Exception as e:
                logger.error(f"Failed to load schema {schema_file}: {str(e)}")
    
    def validate_xml(self, xml_content: str, schema_name: str) -> Tuple[bool, List[str]]:
        """
        Validate XML content against a schema.
        
        Args:
            xml_content: XML content as string
            schema_name: Name of the schema to validate against
            
        Returns:
            Tuple of (is_valid, errors)
        """
        if schema_name not in self.schemas:
            return False, [f"Schema {schema_name} not found"]
            
        try:
            # First check if XML is well-formed
            etree.fromstring(xml_content)
            
            # Then validate against schema
            schema = self.schemas[schema_name]
            validation_errors = schema.iter_errors(xml_content)
            errors = [str(err) for err in validation_errors]
            
            return len(errors) == 0, errors
            
        except XMLSyntaxError as e:
            return False, [f"XML syntax error: {str(e)}"]
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
    
    async def download_schema(self, session: aiohttp.ClientSession, schema_url: str, schema_name: str) -> bool:
        """
        Download and cache an XSD schema.
        
        Args:
            session: aiohttp ClientSession for making HTTP requests
            schema_url: URL to the XSD schema
            schema_name: Name to save the schema as
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        schema_path = Path(self.schema_dir) / f"{schema_name}.xsd"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with session.get(schema_url) as response:
                if response.status == 200:
                    content = await response.text()
                    schema_path.write_text(content)
                    self._load_schemas()  # Reload schemas
                    return True
                logger.error(f"Failed to download schema {schema_name}: HTTP {response.status}")
                return False
        except Exception as e:
            logger.error(f"Failed to download schema {schema_name}: {str(e)}")
            return False
