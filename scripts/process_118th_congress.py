#!/usr/bin/env python3
"""
118th Congress XML Data Processor

Processes downloaded XML files using XSL schemas to extract structured data.
"""

import xml.etree.ElementTree as ET
import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

class Congress118Processor:
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
                logging.FileHandler(
                    "logs/congress118_processor.log",
                    mode='a',
                    encoding='utf-8'
                )
            ]
        )
        self.logger = logging.getLogger("Congress118Processor")
        
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
            
            # Parse bill ID from legis_num (e.g., "S. 1163" -> type="s", number=1163; "H. R. 366" -> type="hr", number=366)
            legis_num = metadata['legis_num']
            if legis_num:
                # Handle different formats: "S. 1163", "H. R. 366", etc.
                if 'H. R.' in legis_num:
                    bill_match = re.match(r'H\. R\. (\d+)', legis_num)
                    if bill_match:
                        metadata['bill_type'] = 'hr'
                        metadata['bill_number'] = int(bill_match.group(1))
                elif 'S.' in legis_num:
                    bill_match = re.match(r'S\. (\d+)', legis_num)
                    if bill_match:
                        metadata['bill_type'] = 's'
                        metadata['bill_number'] = int(bill_match.group(1))
                else:
                    # Fallback to original pattern
                    bill_match = re.match(r'([A-Z]+)\.? (\d+)', legis_num)
                    if bill_match:
                        metadata['bill_type'] = bill_match.group(1).lower()
                        metadata['bill_number'] = int(bill_match.group(2))
                
                if 'bill_type' in metadata and 'bill_number' in metadata:
                    metadata['bill_id'] = f"{metadata['bill_type']}{metadata['bill_number']}"
            
            # Sponsor info
            action = form.find('action')
            if action is not None:
                sponsor = action.find('.//sponsor')
                if sponsor is not None:
                    metadata['sponsor_name_id'] = self._extract_attribute(sponsor, 'name-id')
                    metadata['sponsor_name'] = sponsor.text.strip() if sponsor.text else None
                
                # Action date
                action_date = action.find('action-date')
                if action_date is not None:
                    date_str = self._extract_attribute(action_date, 'date')
                    metadata['introduced_date'] = self._parse_date(date_str)
                
                # Committee referrals
                committees = action.findall('.//committee-name')
                metadata['committees'] = []
                for committee in committees:
                    committee_id = self._extract_attribute(committee, 'committee-id')
                    committee_name = committee.text.strip() if committee.text else None
                    if committee_id and committee_name:
                        metadata['committees'].append({
                            'committee_id': committee_id,
                            'name': committee_name
                        })
        
        # Dublin Core metadata
        dc_metadata = root.find('.//dublinCore')
        if dc_metadata is not None:
            metadata['title'] = self._extract_text(dc_metadata, 'dc:title')
            metadata['publisher'] = self._extract_text(dc_metadata, 'dc:publisher')
            metadata['date'] = self._extract_text(dc_metadata, 'dc:date')
        
        # Bill stage
        metadata['bill_stage'] = self._extract_attribute(root, 'bill-stage')
        metadata['file_path'] = str(xml_path)
        
        return metadata
        
    def _extract_legislative_content(self, root: ET.Element) -> List[Dict]:
        """Extract legislative content sections"""
        content = []
        legis_body = root.find('legis-body')
        
        if legis_body is not None:
            for element in legis_body.iter():
                if element.tag in ['section', 'subsection', 'paragraph', 'subparagraph', 'clause']:
                    section_data = {
                        'element_type': element.tag,
                        'id': self._extract_attribute(element, 'id'),
                        'section_type': self._extract_attribute(element, 'section-type'),
                        'enum': self._extract_attribute(element, 'enum'),
                        'header': self._extract_text(element, 'header'),
                        'text': self._extract_text(element, 'text'),
                        'display_inline': self._extract_attribute(element, 'display-inline')
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
            
            bill_id = metadata.get('bill_id')
            
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
            
            # Insert committees
            for committee in metadata.get('committees', []):
                cursor.execute("""
                    INSERT OR REPLACE INTO committees (committee_id, name, chamber)
                    VALUES (?, ?, ?)
                """, (
                    committee['committee_id'],
                    committee['name'],
                    metadata.get('current_chamber')
                ))
                
                cursor.execute("""
                    INSERT OR REPLACE INTO bill_committees 
                    (bill_id, committee_id, activity_type)
                    VALUES (?, ?, ?)
                """, (
                    bill_id,
                    committee['committee_id'],
                    'referral'
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
            'subparagraph': 4,
            'clause': 5
        }
        return levels.get(element_type, 1)
        
    def process_all_files(self):
        """Process all 118th Congress XML files"""
        congress_dir = self.data_dir / "BILLS" / "bulkdata" / "BILLS" / "118"
        
        if not congress_dir.exists():
            self.logger.error(f"118th Congress directory not found: {congress_dir}")
            return
        
        processed_count = 0
        error_count = 0
        
        # Process all sessions and bill types
        for session_dir in congress_dir.iterdir():
            if session_dir.is_dir() and session_dir.name in ['1', '2']:
                self.logger.info(f"Processing Session {session_dir.name}")
                
                for bill_type_dir in session_dir.iterdir():
                    if bill_type_dir.is_dir():
                        self.logger.info(f"Processing {bill_type_dir.name} bills")
                        
                        for xml_file in bill_type_dir.glob("*.xml"):
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
    """Main entry point for 118th Congress processor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="118th Congress XML Data Processor")
    parser.add_argument('--data-dir', default="data/govinfo", 
                       help="Data directory containing XML files")
    parser.add_argument('--db-path', default="data/govinfo_downloads.db",
                       help="Database path for storing processed data")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = Congress118Processor(args.data_dir, args.db_path)
    
    # Process all files
    processor.process_all_files()

if __name__ == "__main__":
    main()