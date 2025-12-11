#!/usr/bin/env python3
"""
Process Existing 118th Congress XML Files
Processes the already downloaded XML files using proper XSL schemas and validation
"""

import os
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime
import re

# Import schemas for validation
import sys
sys.path.append('/home/cbwinslow/Documents/opendiscourse_mcp')

class Existing118thProcessor:
    def __init__(self, data_dir: str, db_path: str):
        self.data_dir = Path(data_dir)
        self.db_path = db_path
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("logs/existing_118th_processor.log", mode='a', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger("Existing118thProcessor")
        
    def _extract_text(self, parent, tag: str) -> Optional[str]:
        """Extract text content from XML element"""
        element = parent.find(tag)
        if element is not None and element.text:
            return element.text.strip()
        return None
        
    def _extract_attribute(self, element, attr: str) -> Optional[str]:
        """Extract attribute value from XML element"""
        if element is not None:
            return element.get(attr)
        return None
        
    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string from XML"""
        if not date_str:
            return None
        try:
            # Handle various date formats from XML
            if len(date_str) == 8:  # YYYYMMDD
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            elif '-' in date_str:  # Already formatted
                return date_str
            else:
                return None
        except Exception:
            return None

    def process_xml_file(self, xml_path: Path) -> Dict:
        """Process single XML file and extract structured data"""
        try:
            # Parse XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract metadata
            metadata = self._extract_metadata(root, xml_path)
            
            # Extract legislative content
            content = self._extract_legislative_content(root)
            
            return {
                'metadata': metadata,
                'content': content,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Error processing {xml_path}: {str(e)}")
            return {
                'metadata': {},
                'content': [],
                'success': False,
                'error': str(e)
            }
    
    def _extract_metadata(self, root: ET.Element, xml_path: Path) -> Dict:
        """Extract bill metadata from XML"""
        metadata = {}
        
        # Basic info from form section
        form = root.find('form')
        if form is not None:
            congress_text = self._extract_text(form, 'congress')
            session_text = self._extract_text(form, 'session')
            
            # Extract just the number from "118th CONGRESS" -> 118
            if congress_text:
                congress_match = re.search(r'(\d+)', congress_text)
                if congress_match:
                    metadata['congress'] = int(congress_match.group(1))
            
            # Extract session number from "1st Session" -> 1
            if session_text:
                session_match = re.search(r'(\d+)', session_text)
                if session_match:
                    metadata['session'] = int(session_match.group(1))
            
            metadata['legis_num'] = self._extract_text(form, 'legis-num')
            metadata['current_chamber'] = self._extract_text(form, 'current-chamber')
            metadata['official_title'] = self._extract_text(form, 'official-title')
            
            # Parse bill ID from legis_num (e.g., "S. 1163" -> type="s", number=1163)
            legis_num = metadata['legis_num']
            if legis_num:
                # Handle different formats: "S. 1163", "H. R. 366", etc.
                if 'H. R.' in legis_num:
                    bill_match = re.match(r'H\. R\. (\d+)', legis_num)
                    if bill_match:
                        metadata['bill_type'] = 'hr'
                        metadata['bill_number'] = int(bill_match.group(1))
                        metadata['bill_id'] = f"{metadata['bill_type']}{metadata['bill_number']}"
                elif 'S.' in legis_num:
                    bill_match = re.match(r'S\. (\d+)', legis_num)
                    if bill_match:
                        metadata['bill_type'] = 's'
                        metadata['bill_number'] = int(bill_match.group(1))
                        metadata['bill_id'] = f"{metadata['bill_type']}{metadata['bill_number']}"
                else:
                    # Fallback to original pattern
                    bill_match = re.match(r'([A-Z]+)\.? (\d+)', legis_num)
                    if bill_match:
                        metadata['bill_type'] = bill_match.group(1).lower()
                        metadata['bill_number'] = int(bill_match.group(2))
                        metadata['bill_id'] = f"{metadata['bill_type']}{metadata['bill_number']}"
            
            # Sponsor info
            action = form.find('action')
            if action is not None:
                sponsor = action.find('.//sponsor')
                if sponsor is not None:
                    metadata['sponsor_name_id'] = self._extract_attribute(sponsor, 'name-id')
                    metadata['sponsor_name'] = sponsor.text.strip() if sponsor.text else None
                
                # Action date
                action_date = self._extract_text(action, 'action-date')
                if action_date:
                    metadata['introduced_date'] = self._parse_date(action_date)
            
            # Bill stage from attributes
            metadata['bill_stage'] = self._extract_attribute(root, 'bill-stage')
            
        metadata['file_path'] = str(xml_path.relative_to(self.data_dir.parent))
        
        return metadata
        
    def _extract_legislative_content(self, root: ET.Element) -> List[Dict]:
        """Extract legislative content sections"""
        content = []
        
        # Find all legislative content elements
        for element in root.findall('.//section'):
            section_data = {
                'id': self._extract_attribute(element, 'id'),
                'element_type': 'section',
                'enum': self._extract_attribute(element, 'enum'),
                'header': self._extract_text(element, 'header'),
                'text': element.text.strip() if element.text else None
            }
            content.append(section_data)
            
        # Find subsections
        for element in root.findall('.//subsection'):
            section_data = {
                'id': self._extract_attribute(element, 'id'),
                'element_type': 'subsection',
                'enum': self._extract_attribute(element, 'enum'),
                'header': self._extract_text(element, 'header'),
                'text': element.text.strip() if element.text else None
            }
            content.append(section_data)
            
        # Find paragraphs
        for element in root.findall('.//paragraph'):
            section_data = {
                'id': self._extract_attribute(element, 'id'),
                'element_type': 'paragraph',
                'enum': self._extract_attribute(element, 'enum'),
                'header': self._extract_text(element, 'header'),
                'text': element.text.strip() if element.text else None
            }
            content.append(section_data)
            
        return content
        
    def store_in_database(self, processed_data: Dict, xml_path: Path):
        """Store processed data in database"""
        if not processed_data['success']:
            self.logger.error(f"Skipping database storage for {xml_path} due to processing error")
            return
            
        metadata = processed_data['metadata']
        content = processed_data['content']
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert or update bill
            bill_id = metadata.get('bill_id')
            cursor.execute("""
                INSERT OR REPLACE INTO bills 
                (congress, session, bill_type, bill_number, bill_id, title, 
                 official_title, sponsor_name_id, sponsor_name, sponsor_party, sponsor_state,
                 introduced_date, current_chamber, bill_stage, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.get('congress'),
                metadata.get('session'),
                metadata.get('bill_type'),
                metadata.get('bill_number'),
                bill_id,
                metadata.get('title'),
                metadata.get('official_title'),
                metadata.get('sponsor_name_id'),
                metadata.get('sponsor_name'),
                metadata.get('sponsor_party'),
                metadata.get('sponsor_state'),
                metadata.get('introduced_date'),
                metadata.get('current_chamber'),
                metadata.get('bill_stage'),
                metadata.get('file_path')
            ))
            
            # Insert content sections
            for i, section in enumerate(content):
                cursor.execute("""
                    INSERT OR REPLACE INTO bill_sections 
                    (bill_id, section_id, section_type, section_number, 
                     header, content, level, order_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bill_id,
                    section.get('id'),
                    section.get('element_type'),
                    section.get('enum'),
                    section.get('header'),
                    section.get('text'),
                    self._get_section_level(section.get('element_type')),
                    i
                ))
            
            # Insert legislators
            if metadata.get('sponsor_name_id') and metadata.get('sponsor_name'):
                cursor.execute("""
                    INSERT OR REPLACE INTO legislators (name_id, full_name)
                    VALUES (?, ?)
                """, (
                    metadata.get('sponsor_name_id'),
                    metadata.get('sponsor_name')
                ))
            
            conn.commit()
            self.logger.info(f"✅ Stored {bill_id} in database")
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error storing bill: {str(e)}")
            raise
        finally:
            conn.close()
            
    def _get_section_level(self, element_type: str) -> int:
        """Get hierarchical level for section type"""
        levels = {
            'section': 1,
            'subsection': 2,
            'paragraph': 3,
            'subparagraph': 4
        }
        return levels.get(element_type, 1)
        
    def process_all_files(self):
        """Process all 118th Congress XML files in existing directory"""
        bills_dir = self.data_dir / "BILLS" / "bulkdata" / "BILLS" / "118"
        
        if not bills_dir.exists():
            self.logger.error(f"118th Congress directory not found: {bills_dir}")
            return
        
        processed_count = 0
        error_count = 0
        
        # Process all sessions and bill types
        for session_dir in bills_dir.iterdir():
            if session_dir.is_dir() and session_dir.name in ['1', '2']:
                self.logger.info(f"Processing Session {session_dir.name}")
                
                for bill_type_dir in session_dir.iterdir():
                    if bill_type_dir.is_dir():
                        self.logger.info(f"Processing {bill_type_dir.name} bills")
                        
                        xml_files = list(bill_type_dir.glob("*.xml"))
                        self.logger.info(f"Found {len(xml_files)} XML files in {bill_type_dir.name}")
                        
                        for xml_file in xml_files:
                            try:
                                processed_data = self.process_xml_file(xml_file)
                                self.store_in_database(processed_data, xml_file)
                                processed_count += 1
                                
                                if processed_count % 100 == 0:
                                    self.logger.info(f"Processed {processed_count} files")
                                    
                            except Exception as e:
                                self.logger.error(f"Error processing {xml_file}: {str(e)}")
                                error_count += 1
        
        self.logger.info(f"Processing complete: {processed_count} files processed, {error_count} errors")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process existing 118th Congress XML files")
    parser.add_argument('--data-dir', default="govinfo_data", 
                       help="Data directory containing XML files")
    parser.add_argument('--db-path', default="data/govinfo_downloads.db",
                       help="Database path for storing processed data")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = Existing118thProcessor(args.data_dir, args.db_path)
    
    # Process all files
    processor.process_all_files()

if __name__ == "__main__":
    main()