-- GovInfo Bulk Data Schema for PostgreSQL
-- Generic tables for various collection types
-- Bills (from BILLS collection)
CREATE TABLE IF NOT EXISTS govinfo_bills (
    id SERIAL PRIMARY KEY,
    congress INTEGER NOT NULL,
    session INTEGER,
    bill_type VARCHAR(20) NOT NULL,
    bill_number INTEGER NOT NULL,
    bill_id VARCHAR(50) UNIQUE NOT NULL,
    title TEXT,
    official_title TEXT,
    sponsor_name_id VARCHAR(20),
    sponsor_name TEXT,
    introduced_date DATE,
    current_chamber VARCHAR(20),
    bill_stage VARCHAR(50),
    file_path TEXT,
    raw_xml TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Bill Status (from BILLSTATUS collection)
CREATE TABLE IF NOT EXISTS govinfo_bill_status (
    id SERIAL PRIMARY KEY,
    bill_id VARCHAR(50) UNIQUE NOT NULL,
    congress INTEGER NOT NULL,
    bill_type VARCHAR(20),
    bill_number INTEGER,
    origin_chamber VARCHAR(50),
    latest_action_date DATE,
    latest_action_text TEXT,
    policy_area TEXT,
    file_path TEXT,
    raw_xml TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Bill Summaries (from BILLSUM collection)
CREATE TABLE IF NOT EXISTS govinfo_bill_summaries (
    id SERIAL PRIMARY KEY,
    bill_id VARCHAR(50) NOT NULL,
    congress INTEGER,
    version_code VARCHAR(20),
    action_date DATE,
    action_desc VARCHAR(100),
    summary_text TEXT,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Code of Federal Regulations (from CFR collection)
CREATE TABLE IF NOT EXISTS govinfo_cfr (
    id SERIAL PRIMARY KEY,
    cfr_title INTEGER NOT NULL,
    cfr_part VARCHAR(50),
    cfr_section VARCHAR(100),
    year INTEGER,
    volume VARCHAR(20),
    subject TEXT,
    authority TEXT,
    source TEXT,
    content TEXT,
    file_path TEXT,
    raw_xml TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Federal Register (from FR collection)
CREATE TABLE IF NOT EXISTS govinfo_federal_register (
    id SERIAL PRIMARY KEY,
    document_number VARCHAR(50) UNIQUE,
    document_type VARCHAR(50),
    agency VARCHAR(200),
    title TEXT,
    publication_date DATE,
    effective_date DATE,
    cfr_references TEXT,
    action VARCHAR(100),
    summary TEXT,
    content TEXT,
    file_path TEXT,
    raw_xml TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Public Laws (from PLAW collection)
CREATE TABLE IF NOT EXISTS govinfo_public_laws (
    id SERIAL PRIMARY KEY,
    law_number VARCHAR(50) UNIQUE NOT NULL,
    congress INTEGER NOT NULL,
    law_type VARCHAR(20),
    title TEXT,
    enactment_date DATE,
    bill_id VARCHAR(50),
    statutes_at_large_cite TEXT,
    file_path TEXT,
    raw_xml TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Statutes at Large (from STATUTE collection)
CREATE TABLE IF NOT EXISTS govinfo_statutes (
    id SERIAL PRIMARY KEY,
    volume INTEGER NOT NULL,
    page INTEGER,
    congress INTEGER,
    session INTEGER,
    statute_cite VARCHAR(100) UNIQUE,
    title TEXT,
    enactment_date DATE,
    content TEXT,
    file_path TEXT,
    raw_xml TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Generic raw XML storage for any collection
CREATE TABLE IF NOT EXISTS govinfo_raw_documents (
    id SERIAL PRIMARY KEY,
    collection VARCHAR(50) NOT NULL,
    document_id VARCHAR(200) NOT NULL,
    file_path TEXT NOT NULL,
    raw_xml TEXT,
    parsed_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(collection, document_id)
);
-- Indexes
CREATE INDEX IF NOT EXISTS idx_govinfo_bills_congress ON govinfo_bills(congress);
CREATE INDEX IF NOT EXISTS idx_govinfo_bills_type ON govinfo_bills(bill_type);
CREATE INDEX IF NOT EXISTS idx_govinfo_bill_status_congress ON govinfo_bill_status(congress);
CREATE INDEX IF NOT EXISTS idx_govinfo_cfr_title ON govinfo_cfr(cfr_title);
CREATE INDEX IF NOT EXISTS idx_govinfo_fr_date ON govinfo_federal_register(publication_date);
CREATE INDEX IF NOT EXISTS idx_govinfo_plaw_congress ON govinfo_public_laws(congress);
CREATE INDEX IF NOT EXISTS idx_govinfo_statutes_volume ON govinfo_statutes(volume);
CREATE INDEX IF NOT EXISTS idx_govinfo_raw_collection ON govinfo_raw_documents(collection);