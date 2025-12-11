-- Database schema extension for 118th Congress legislative data
-- This extends the existing schema with tables for processed XML data

-- Bills table
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    congress INTEGER NOT NULL,
    session INTEGER NOT NULL,
    bill_type VARCHAR(20) NOT NULL,
    bill_number INTEGER NOT NULL,
    bill_id VARCHAR(50) UNIQUE NOT NULL,
    title TEXT,
    official_title TEXT,
    sponsor_name_id VARCHAR(20),
    sponsor_name TEXT,
    sponsor_party VARCHAR(10),
    sponsor_state VARCHAR(10),
    introduced_date DATE,
    current_chamber VARCHAR(20),
    bill_stage VARCHAR(50),
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bill content sections
CREATE TABLE IF NOT EXISTS bill_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id VARCHAR(50) NOT NULL,
    section_id VARCHAR(100),
    section_type VARCHAR(50),
    section_number VARCHAR(20),
    header TEXT,
    content TEXT,
    parent_section_id VARCHAR(100),
    level INTEGER DEFAULT 1,
    order_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE
);

-- Legislators
CREATE TABLE IF NOT EXISTS legislators (
    name_id VARCHAR(20) PRIMARY KEY,
    full_name TEXT NOT NULL,
    state VARCHAR(10),
    party VARCHAR(10),
    chamber VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Committees
CREATE TABLE IF NOT EXISTS committees (
    committee_id VARCHAR(20) PRIMARY KEY,
    name TEXT NOT NULL,
    chamber VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bill cosponsors
CREATE TABLE IF NOT EXISTS bill_cosponsors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id VARCHAR(50) NOT NULL,
    name_id VARCHAR(20) NOT NULL,
    cosponsored_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
    FOREIGN KEY (name_id) REFERENCES legislators(name_id) ON DELETE CASCADE
);

-- Bill committees
CREATE TABLE IF NOT EXISTS bill_committees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id VARCHAR(50) NOT NULL,
    committee_id VARCHAR(20) NOT NULL,
    activity_type VARCHAR(50) DEFAULT 'referral',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
    FOREIGN KEY (committee_id) REFERENCES committees(committee_id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_bills_congress_session ON bills(congress, session);
CREATE INDEX IF NOT EXISTS idx_bills_bill_type ON bills(bill_type);
CREATE INDEX IF NOT EXISTS idx_bills_sponsor ON bills(sponsor_name_id);
CREATE INDEX IF NOT EXISTS idx_bills_introduced_date ON bills(introduced_date);
CREATE INDEX IF NOT EXISTS idx_bill_sections_bill_id ON bill_sections(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_sections_section_id ON bill_sections(section_id);
CREATE INDEX IF NOT EXISTS idx_legislators_name_id ON legislators(name_id);
CREATE INDEX IF NOT EXISTS idx_legislators_state ON legislators(state);
CREATE INDEX IF NOT EXISTS idx_legislators_party ON legislators(party);
CREATE INDEX IF NOT EXISTS idx_committees_committee_id ON committees(committee_id);
CREATE INDEX IF NOT EXISTS idx_committees_chamber ON committees(chamber);
CREATE INDEX IF NOT EXISTS idx_bill_cosponsors_bill_id ON bill_cosponsors(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_cosponsors_name_id ON bill_cosponsors(name_id);
CREATE INDEX IF NOT EXISTS idx_bill_committees_bill_id ON bill_committees(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_committees_committee_id ON bill_committees(committee_id);