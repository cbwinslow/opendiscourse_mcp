#!/usr/bin/env python3
"""
Generic GovInfo XML Ingestion Framework
Modular system for ingesting various GovInfo collection types into PostgreSQL.
"""
import os
import sys
import re
import logging
import argparse
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
import psycopg2
from psycopg2.extras import Json
from lxml import etree

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/govinfo_ingestion.log", mode='a')
    ]
)
logger = logging.getLogger("GovInfoIngest")


class BaseParser(ABC):
    """Abstract base class for collection-specific parsers"""
    
    COLLECTION_NAME: str = None
    TABLE_NAME: str = None
    
    def __init__(self):
        self.ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
    
    @abstractmethod
    def parse(self, file_path: Path, tree: etree._ElementTree) -> Optional[Dict[str, Any]]:
        """Parse XML tree and return data dict for insertion"""
        pass
    
    @abstractmethod
    def get_insert_sql(self) -> str:
        """Return the INSERT SQL statement"""
        pass
    
    @abstractmethod
    def get_values(self, data: Dict[str, Any]) -> tuple:
        """Extract values tuple from parsed data for SQL insertion"""
        pass
    
    def get_unique_id(self, data: Dict[str, Any]) -> str:
        """Return unique identifier for deduplication"""
        return data.get('file_path', '')


class BillsParser(BaseParser):
    """Parser for BILLS collection"""
    COLLECTION_NAME = "BILLS"
    TABLE_NAME = "govinfo_bills"
    
    def parse(self, file_path: Path, tree: etree._ElementTree) -> Optional[Dict[str, Any]]:
        root = tree.getroot()
        data = {'file_path': str(file_path)}
        
        # Dublin Core date
        dc_date = root.find('.//dc:date', self.ns)
        data['introduced_date'] = dc_date.text if dc_date is not None else None
        
        # Form metadata
        form = root.find('form') or root
        
        congress_el = form.find('.//congress')
        data['congress'] = int(''.join(filter(str.isdigit, congress_el.text))) if congress_el is not None and congress_el.text else None
        
        session_el = form.find('.//session')
        data['session'] = int(''.join(filter(str.isdigit, session_el.text))) if session_el is not None and session_el.text else None
        
        legis_num = form.find('.//legis-num')
        if legis_num is not None and legis_num.text:
            match = re.search(r'([A-Za-z\.\s]+)\s*(\d+)', legis_num.text)
            if match:
                data['bill_type'] = match.group(1).strip().replace('.', '').replace(' ', '').upper()
                data['bill_number'] = int(match.group(2))
        
        data['bill_id'] = f"{data.get('congress', 0)}-{data.get('bill_type', 'UNK')}-{data.get('bill_number', 0)}".lower()
        
        title_el = form.find('.//official-title')
        data['official_title'] = title_el.text.strip() if title_el is not None and title_el.text else None
        
        # Sponsor
        sponsor = root.find('.//sponsor')
        if sponsor is not None:
            data['sponsor_name_id'] = sponsor.get('name-id')
            data['sponsor_name'] = sponsor.text.strip() if sponsor.text else None
        
        # Stage from root element
        data['bill_stage'] = root.get('bill-stage') or root.get('resolution-stage')
        
        return data
    
    def get_insert_sql(self) -> str:
        return """
            INSERT INTO govinfo_bills (
                congress, session, bill_type, bill_number, bill_id, 
                official_title, sponsor_name_id, sponsor_name, introduced_date, 
                bill_stage, file_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (bill_id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
        """
    
    def get_values(self, data: Dict[str, Any]) -> tuple:
        return (
            data.get('congress'),
            data.get('session'),
            data.get('bill_type'),
            data.get('bill_number'),
            data.get('bill_id'),
            data.get('official_title'),
            data.get('sponsor_name_id'),
            data.get('sponsor_name'),
            data.get('introduced_date'),
            data.get('bill_stage'),
            data.get('file_path')
        )
    
    def get_unique_id(self, data: Dict[str, Any]) -> str:
        return data.get('bill_id', '')


class BillStatusParser(BaseParser):
    """Parser for BILLSTATUS collection"""
    COLLECTION_NAME = "BILLSTATUS"
    TABLE_NAME = "govinfo_bill_status"
    
    def parse(self, file_path: Path, tree: etree._ElementTree) -> Optional[Dict[str, Any]]:
        root = tree.getroot()
        data = {'file_path': str(file_path)}
        
        bill = root.find('.//bill')
        if bill is None:
            return None
        
        data['congress'] = int(bill.findtext('congress', 0))
        data['bill_type'] = bill.findtext('type')
        data['bill_number'] = int(bill.findtext('number', 0))
        data['origin_chamber'] = bill.findtext('originChamber')
        
        data['bill_id'] = f"{data['congress']}-{data['bill_type']}-{data['bill_number']}".lower()
        
        latest_action = bill.find('.//latestAction')
        if latest_action is not None:
            data['latest_action_date'] = latest_action.findtext('actionDate')
            data['latest_action_text'] = latest_action.findtext('text')
        
        data['policy_area'] = bill.findtext('.//policyArea/name')
        
        return data
    
    def get_insert_sql(self) -> str:
        return """
            INSERT INTO govinfo_bill_status (
                bill_id, congress, bill_type, bill_number, origin_chamber,
                latest_action_date, latest_action_text, policy_area, file_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (bill_id) DO UPDATE SET 
                latest_action_date = EXCLUDED.latest_action_date,
                latest_action_text = EXCLUDED.latest_action_text
        """
    
    def get_values(self, data: Dict[str, Any]) -> tuple:
        return (
            data.get('bill_id'),
            data.get('congress'),
            data.get('bill_type'),
            data.get('bill_number'),
            data.get('origin_chamber'),
            data.get('latest_action_date'),
            data.get('latest_action_text'),
            data.get('policy_area'),
            data.get('file_path')
        )
    
    def get_unique_id(self, data: Dict[str, Any]) -> str:
        return data.get('bill_id', '')


class CFRParser(BaseParser):
    """Parser for CFR collection"""
    COLLECTION_NAME = "CFR"
    TABLE_NAME = "govinfo_cfr"
    
    def parse(self, file_path: Path, tree: etree._ElementTree) -> Optional[Dict[str, Any]]:
        root = tree.getroot()
        data = {'file_path': str(file_path)}
        
        # Extract from path: CFR/YEAR/titleX/CFR-YEAR-titleX-partY.xml
        path_parts = str(file_path).split('/')
        for part in path_parts:
            if part.startswith('title') and part[5:].isdigit():
                data['cfr_title'] = int(part[5:])
            if re.match(r'\d{4}', part):
                data['year'] = int(part)
        
        # Try extracting from filename
        filename = file_path.name
        match = re.search(r'CFR-(\d{4})-title(\d+)(?:-vol(\d+))?(?:-part(\d+))?', filename)
        if match:
            data['year'] = int(match.group(1))
            data['cfr_title'] = int(match.group(2))
            if match.group(3):
                data['volume'] = match.group(3)
            if match.group(4):
                data['cfr_part'] = match.group(4)
        
        # Content from XML
        title_el = root.find('.//TITLESTMT/TITLE') or root.find('.//TITLE')
        data['subject'] = title_el.text if title_el is not None else None
        
        auth = root.find('.//AUTH')
        data['authority'] = ''.join(auth.itertext()).strip() if auth is not None else None
        
        source = root.find('.//SOURCE')
        data['source'] = ''.join(source.itertext()).strip() if source is not None else None
        
        return data
    
    def get_insert_sql(self) -> str:
        return """
            INSERT INTO govinfo_cfr (
                cfr_title, cfr_part, year, volume, subject, authority, source, file_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
    
    def get_values(self, data: Dict[str, Any]) -> tuple:
        return (
            data.get('cfr_title'),
            data.get('cfr_part'),
            data.get('year'),
            data.get('volume'),
            data.get('subject'),
            data.get('authority'),
            data.get('source'),
            data.get('file_path')
        )


class FRParser(BaseParser):
    """Parser for Federal Register collection"""
    COLLECTION_NAME = "FR"
    TABLE_NAME = "govinfo_federal_register"
    
    def parse(self, file_path: Path, tree: etree._ElementTree) -> Optional[Dict[str, Any]]:
        root = tree.getroot()
        data = {'file_path': str(file_path)}
        
        # Document metadata
        data['document_number'] = root.findtext('.//DOCNO') or root.findtext('.//FRDOC')
        data['document_type'] = root.tag
        
        agency = root.find('.//AGENCY')
        data['agency'] = agency.text if agency is not None else None
        
        subject = root.find('.//SUBJECT') or root.find('.//TITLE')
        data['title'] = subject.text if subject is not None else None
        
        # Dates
        date = root.find('.//DATE')
        if date is not None and date.text:
            try:
                data['publication_date'] = datetime.strptime(date.text.strip(), '%B %d, %Y').date()
            except ValueError:
                data['publication_date'] = None
        
        eff_date = root.find('.//EFFDATE')
        data['effective_date'] = eff_date.text if eff_date is not None else None
        
        action = root.find('.//ACTION')
        data['action'] = ''.join(action.itertext()).strip() if action is not None else None
        
        summary = root.find('.//SUMMARY')
        data['summary'] = ''.join(summary.itertext()).strip() if summary is not None else None
        
        return data
    
    def get_insert_sql(self) -> str:
        return """
            INSERT INTO govinfo_federal_register (
                document_number, document_type, agency, title, publication_date,
                effective_date, action, summary, file_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (document_number) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
        """
    
    def get_values(self, data: Dict[str, Any]) -> tuple:
        return (
            data.get('document_number'),
            data.get('document_type'),
            data.get('agency'),
            data.get('title'),
            data.get('publication_date'),
            data.get('effective_date'),
            data.get('action'),
            data.get('summary'),
            data.get('file_path')
        )
    
    def get_unique_id(self, data: Dict[str, Any]) -> str:
        return data.get('document_number', '')


class PLAWParser(BaseParser):
    """Parser for Public Laws collection"""
    COLLECTION_NAME = "PLAW"
    TABLE_NAME = "govinfo_public_laws"
    
    def parse(self, file_path: Path, tree: etree._ElementTree) -> Optional[Dict[str, Any]]:
        root = tree.getroot()
        data = {'file_path': str(file_path)}
        
        # Extract from filename: PLAW-113publ1.xml
        filename = file_path.name
        match = re.search(r'PLAW-(\d+)(publ|pvt)(\d+)', filename)
        if match:
            data['congress'] = int(match.group(1))
            data['law_type'] = 'public' if match.group(2) == 'publ' else 'private'
            law_num = match.group(3)
            data['law_number'] = f"{data['congress']}-{data['law_type'][:3]}-{law_num}"
        
        # Title from XML
        title_el = root.find('.//dc:title', self.ns) or root.find('.//title') or root.find('.//TITLE')
        data['title'] = title_el.text if title_el is not None else None
        
        # Enactment date
        date_el = root.find('.//dc:date', self.ns) or root.find('.//approved')
        data['enactment_date'] = date_el.text if date_el is not None else None
        
        # Bill reference
        bill_ref = root.find('.//bill-ref') or root.find('.//legis-num')
        if bill_ref is not None:
            data['bill_id'] = bill_ref.text
        
        return data
    
    def get_insert_sql(self) -> str:
        return """
            INSERT INTO govinfo_public_laws (
                law_number, congress, law_type, title, enactment_date, bill_id, file_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (law_number) DO NOTHING
        """
    
    def get_values(self, data: Dict[str, Any]) -> tuple:
        return (
            data.get('law_number'),
            data.get('congress'),
            data.get('law_type'),
            data.get('title'),
            data.get('enactment_date'),
            data.get('bill_id'),
            data.get('file_path')
        )
    
    def get_unique_id(self, data: Dict[str, Any]) -> str:
        return data.get('law_number', '')


class StatuteParser(BaseParser):
    """Parser for Statutes at Large collection"""
    COLLECTION_NAME = "STATUTE"
    TABLE_NAME = "govinfo_statutes"
    
    def parse(self, file_path: Path, tree: etree._ElementTree) -> Optional[Dict[str, Any]]:
        root = tree.getroot()
        data = {'file_path': str(file_path)}
        
        # Extract from path/filename: STATUTE-VOL-Pg.xml
        filename = file_path.name
        match = re.search(r'STATUTE-(\d+)-Pg(\d+)', filename)
        if match:
            data['volume'] = int(match.group(1))
            data['page'] = int(match.group(2))
            data['statute_cite'] = f"{data['volume']} Stat. {data['page']}"
        
        # Try XML metadata
        volume_el = root.find('.//volume')
        if volume_el is not None and volume_el.text:
            data['volume'] = int(volume_el.text)
        
        congress_el = root.find('.//congress')
        if congress_el is not None and congress_el.text:
            data['congress'] = int(''.join(filter(str.isdigit, congress_el.text)))
        
        session_el = root.find('.//session')
        if session_el is not None and session_el.text:
            data['session'] = int(''.join(filter(str.isdigit, session_el.text)))
        
        title_el = root.find('.//dc:title', self.ns) or root.find('.//title')
        data['title'] = title_el.text if title_el is not None else None
        
        date_el = root.find('.//dc:date', self.ns) or root.find('.//date')
        data['enactment_date'] = date_el.text if date_el is not None else None
        
        return data
    
    def get_insert_sql(self) -> str:
        return """
            INSERT INTO govinfo_statutes (
                volume, page, congress, session, statute_cite, title, enactment_date, file_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (statute_cite) DO NOTHING
        """
    
    def get_values(self, data: Dict[str, Any]) -> tuple:
        return (
            data.get('volume'),
            data.get('page'),
            data.get('congress'),
            data.get('session'),
            data.get('statute_cite'),
            data.get('title'),
            data.get('enactment_date'),
            data.get('file_path')
        )
    
    def get_unique_id(self, data: Dict[str, Any]) -> str:
        return data.get('statute_cite', '')


class BillSumParser(BaseParser):
    """Parser for BILLSUM collection"""
    COLLECTION_NAME = "BILLSUM"
    TABLE_NAME = "govinfo_bill_summaries"
    
    def parse(self, file_path: Path, tree: etree._ElementTree) -> Optional[Dict[str, Any]]:
        root = tree.getroot()
        data = {'file_path': str(file_path)}
        
        # Bill identifier
        item = root.find('.//item') or root
        
        data['congress'] = item.findtext('.//congress')
        bill_type = item.findtext('.//billType') or item.findtext('.//type')
        bill_number = item.findtext('.//billNumber') or item.findtext('.//number')
        
        if data['congress'] and bill_type and bill_number:
            data['bill_id'] = f"{data['congress']}-{bill_type}-{bill_number}".lower()
        else:
            # Try filename
            match = re.search(r'BILLSUM-(\d+)([a-z]+)(\d+)', file_path.name)
            if match:
                data['congress'] = int(match.group(1))
                data['bill_id'] = f"{match.group(1)}-{match.group(2)}-{match.group(3)}".lower()
        
        data['version_code'] = item.findtext('.//versionCode')
        data['action_date'] = item.findtext('.//actionDate')
        data['action_desc'] = item.findtext('.//actionDesc')
        
        summary = item.find('.//summary') or item.find('.//text')
        data['summary_text'] = ''.join(summary.itertext()).strip() if summary is not None else None
        
        return data
    
    def get_insert_sql(self) -> str:
        return """
            INSERT INTO govinfo_bill_summaries (
                bill_id, congress, version_code, action_date, action_desc, summary_text, file_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
    
    def get_values(self, data: Dict[str, Any]) -> tuple:
        return (
            data.get('bill_id'),
            int(data['congress']) if data.get('congress') else None,
            data.get('version_code'),
            data.get('action_date'),
            data.get('action_desc'),
            data.get('summary_text'),
            data.get('file_path')
        )


# Parser Registry
PARSERS: Dict[str, type] = {
    'BILLS': BillsParser,
    'BILLSTATUS': BillStatusParser,
    'BILLSUM': BillSumParser,
    'CFR': CFRParser,
    'FR': FRParser,
    'PLAW': PLAWParser,
    'STATUTE': StatuteParser,
}


class GovInfoIngester:
    """Main ingestion orchestrator"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.processed = 0
        self.errors = 0
    
    def get_connection(self):
        return psycopg2.connect(**self.db_config)
    
    def ingest_file(self, file_path: Path, parser: BaseParser) -> bool:
        """Ingest a single file using the appropriate parser"""
        try:
            tree = etree.parse(str(file_path))
            data = parser.parse(file_path, tree)
            
            if not data:
                return False
            
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                cur.execute(parser.get_insert_sql(), parser.get_values(data))
                conn.commit()
                return True
            finally:
                conn.close()
                
        except Exception as e:
            logger.debug(f"Error ingesting {file_path}: {e}")
            return False
    
    def ingest_collection(self, collection: str, data_dir: str, workers: int = 10):
        """Ingest all files from a collection"""
        if collection not in PARSERS:
            logger.error(f"Unknown collection: {collection}. Available: {list(PARSERS.keys())}")
            return
        
        parser_class = PARSERS[collection]
        parser = parser_class()
        
        # Find XML files
        path = Path(data_dir) / collection
        if not path.exists():
            path = Path(data_dir)
        
        xml_files = list(path.glob('**/*.xml'))
        total = len(xml_files)
        logger.info(f"Found {total} XML files for {collection}")
        
        success = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self.ingest_file, f, parser_class()): f 
                for f in xml_files
            }
            
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                if future.result():
                    success += 1
                
                if (i + 1) % 500 == 0:
                    logger.info(f"Progress: {i+1}/{total} ({success} successful)")
        
        logger.info(f"Completed {collection}: {success}/{total} files ingested")


def main():
    parser = argparse.ArgumentParser(description="GovInfo XML Ingestion")
    parser.add_argument('--collection', required=True, 
                       choices=list(PARSERS.keys()), 
                       help="Collection to ingest")
    parser.add_argument('--input', default='govinfo_data', help="Input directory")
    parser.add_argument('--workers', type=int, default=10, help="Concurrent workers")
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--database', default='opendiscourse')
    parser.add_argument('--user', default='opendiscourse')
    parser.add_argument('--password', default='opendiscourse123')
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.host,
        'database': args.database,
        'user': args.user,
        'password': args.password
    }
    
    ingester = GovInfoIngester(db_config)
    ingester.ingest_collection(args.collection, args.input, args.workers)


if __name__ == "__main__":
    main()
