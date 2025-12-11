#!/usr/bin/env python3
"""
GovInfo XML Ingestion Script
Ingests downloaded Bill XML files into the OpenDiscourse PostgreSQL database.
"""
import os
import sys
import logging
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import execute_values
from lxml import etree

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
from config.global_settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/xml_ingestion.log")
    ]
)
logger = logging.getLogger("XMLIngest")

class XMLIngester:
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.ns = {'dc': 'http://purl.org/dc/elements/1.1/'} # Dublin Core namespace

    def get_db_connection(self):
        return psycopg2.connect(**self.db_config)

    def parse_xml_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single XML file and extract relevant data"""
        try:
            tree = etree.parse(str(file_path))
            root = tree.getroot()
            
            # Extract Metadata
            metadata = {}
            
            # Dublin Core Metadata
            dc_date = root.find('.//dc:date', self.ns)
            metadata['date'] = dc_date.text if dc_date is not None else None
            
            # Form Metadata
            form = root.find('form')
            if form is None:
                # Fallback for some XMLs that might have different structure
                form = root
            
            congress_el = form.find('.//congress')
            metadata['congress'] = ''.join(filter(str.isdigit, congress_el.text)) if congress_el is not None and congress_el.text else None
            
            session_el = form.find('.//session')
            metadata['session'] = ''.join(filter(str.isdigit, session_el.text)) if session_el is not None and session_el.text else None
            
            legis_num_el = form.find('.//legis-num')
            legis_num = legis_num_el.text if legis_num_el is not None else ""
            # Parse legis_num (e.g., S. RES. 479)
            # This requires robust regex usually, simplified here
            import re
            bill_match = re.search(r'([A-Za-z\.\s]+)\s*(\d+)', legis_num)
            if bill_match:
                metadata['bill_type'] = bill_match.group(1).strip().replace('.', '').upper()
                metadata['bill_number'] = bill_match.group(2)
            else:
                metadata['bill_type'] = 'UNKNOWN'
                metadata['bill_number'] = '0'

            metadata['bill_id'] = f"{metadata['congress']}-{metadata['bill_type']}-{metadata['bill_number']}".lower().replace(' ', '')
            
            # Title
            title_el = form.find('.//official-title')
            metadata['official_title'] = title_el.text.strip() if title_el is not None and title_el.text else None
            
            # Sponsor
            action = form.find('.//action')
            if action is not None:
                sponsor = action.find('.//sponsor')
                if sponsor is not None:
                    metadata['sponsor_name_id'] = sponsor.get('name-id')
                    metadata['sponsor_name'] = sponsor.text.strip() if sponsor.text else None
            
            # Sections / Text extraction (simplified)
            # Ideally walk the 'resolution-body' or 'legis-body'
            body = root.find('resolution-body') or root.find('legis-body')
            sections = []
            if body is not None:
                for idx, section in enumerate(body.iter('section')):
                    sec_id = section.get('id')
                    header = section.find('header')
                    text_content = "".join(section.itertext())
                    sections.append({
                        'section_id': sec_id,
                        'header': header.text if header is not None else None,
                        'content': text_content,
                        'order_index': idx
                    })
            
            return {
                'file_path': str(file_path),
                'metadata': metadata,
                'sections': sections
            }

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None

    def ingest_file(self, file_path: Path):
        """Worker function to process a single file"""
        data = self.parse_xml_file(file_path)
        if not data:
            return

        meta = data['metadata']
        
        # Validate basic requirements
        if not meta['congress'] or not meta['bill_number']:
            logger.warning(f"Skipping {file_path}: Missing congress or bill number")
            return

        conn = None
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            # Upsert Bill
            cur.execute("""
                INSERT INTO bills (
                    congress, session, bill_type, bill_number, bill_id, 
                    official_title, sponsor_name_id, sponsor_name, introduced_date, file_path
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (bill_id) DO UPDATE SET
                    official_title = EXCLUDED.official_title,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                int(meta['congress']),
                int(meta['session']) if meta['session'] else 0,
                meta['bill_type'],
                int(meta['bill_number']),
                meta['bill_id'],
                meta['official_title'],
                meta.get('sponsor_name_id'),
                meta.get('sponsor_name'),
                meta.get('date'),
                data['file_path']
            ))
            
            # Sections
            # First clean existing sections for this bill to avoid duplication on re-run
            cur.execute("DELETE FROM bill_sections WHERE bill_id = %s", (meta['bill_id'],))
            
            for sec in data['sections']:
                cur.execute("""
                    INSERT INTO bill_sections (
                        bill_id, section_id, header, content, order_index
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    meta['bill_id'],
                    sec['section_id'],
                    sec['header'],
                    sec['content'],
                    sec.get('order_index', 0)
                ))
            
            # Commit transaction
            conn.commit()
            logger.info(f"Ingested {meta['bill_id']}")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error for {file_path}: {e}")
        finally:
            if conn:
                conn.close()

    def process_directory(self, data_dir: str, workers: int = 10):
        """Process all XML files in directory recursively"""
        path = Path(data_dir)
        xml_files = list(path.glob('**/*.xml'))
        logger.info(f"Found {len(xml_files)} XML files to process")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(self.ingest_file, f) for f in xml_files]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Worker exception: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest GovInfo XML files into SQL")
    parser.add_argument('--input', default='govinfo_data', help="Input directory")
    parser.add_argument('--workers', type=int, default=10, help="Concurrency")
    
    args = parser.parse_args()
    
    # DB Config - hardcoded based on user request, ideally from settings
    db_config = {
        'host': 'localhost',
        'database': 'opendiscourse',
        'user': 'opendiscourse',
        'password': 'opendiscourse123'
    }
    
    ingester = XMLIngester(db_config)
    ingester.process_directory(args.input, args.workers)

if __name__ == "__main__":
    main()
