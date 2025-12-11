#!/usr/bin/env python3
"""
Comprehensive 118th Congress Data Verification and Testing
Validates complete dataset ingestion and tests MCP server performance
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging

class Comprehensive118thVerifier:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("logs/comprehensive_118th_verification.log", mode='a', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger("Comprehensive118thVerifier")
        
    def verify_data_integrity(self) -> Dict:
        """Verify complete dataset integrity"""
        self.logger.info("Starting comprehensive data integrity verification")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        verification_results = {}
        
        try:
            # 1. Bill count verification
            cursor.execute("SELECT COUNT(*) FROM bills WHERE congress = 118")
            total_bills = cursor.fetchone()[0]
            verification_results['total_bills'] = total_bills
            
            # 2. Bill types distribution
            cursor.execute("""
                SELECT bill_type, COUNT(*) as count 
                FROM bills 
                WHERE congress = 118 
                GROUP BY bill_type
                ORDER BY count DESC
            """)
            bill_types = dict(cursor.fetchall())
            verification_results['bill_types'] = bill_types
            
            # 3. Session distribution
            cursor.execute("""
                SELECT session, COUNT(*) as count 
                FROM bills 
                WHERE congress = 118 
                GROUP BY session
                ORDER BY session
            """)
            sessions = dict(cursor.fetchall())
            verification_results['sessions'] = sessions
            
            # 4. Content sections verification
            cursor.execute("""
                SELECT COUNT(*) FROM bill_sections bs
                JOIN bills b ON bs.bill_id = b.bill_id
                WHERE b.congress = 118
            """)
            total_sections = cursor.fetchone()[0]
            verification_results['total_sections'] = total_sections
            
            # 5. Section types distribution
            cursor.execute("""
                SELECT bs.section_type, COUNT(*) as count 
                FROM bill_sections bs
                JOIN bills b ON bs.bill_id = b.bill_id
                WHERE b.congress = 118
                GROUP BY bs.section_type
                ORDER BY count DESC
            """)
            section_types = dict(cursor.fetchall())
            verification_results['section_types'] = section_types
            
            # 6. Sponsor verification
            cursor.execute("""
                SELECT COUNT(DISTINCT sponsor_name_id) 
                FROM bills 
                WHERE congress = 118 AND sponsor_name_id IS NOT NULL
            """)
            unique_sponsors = cursor.fetchone()[0]
            verification_results['unique_sponsors'] = unique_sponsors
            
            # 7. Content completeness (bills with sections)
            cursor.execute("""
                SELECT COUNT(DISTINCT b.bill_id) 
                FROM bills b
                LEFT JOIN bill_sections bs ON b.bill_id = bs.bill_id
                WHERE b.congress = 118
            """)
            bills_with_content = cursor.fetchone()[0]
            content_completeness = (bills_with_content / total_bills * 100) if total_bills > 0 else 0
            verification_results['content_completeness'] = {
                'bills_with_content': bills_with_content,
                'total_bills': total_bills,
                'completeness_percentage': content_completeness
            }
            
            # 8. Data quality checks
            quality_checks = {}
            
            # Check for missing essential fields
            cursor.execute("""
                SELECT COUNT(*) FROM bills 
                WHERE congress = 118 AND (bill_id IS NULL OR bill_type IS NULL OR bill_number IS NULL)
            """)
            quality_checks['missing_essential_fields'] = cursor.fetchone()[0]
            
            # Check for duplicate bill_ids
            cursor.execute("""
                SELECT bill_id, COUNT(*) as count 
                FROM bills 
                WHERE congress = 118 
                GROUP BY bill_id 
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            quality_checks['duplicate_bill_ids'] = len(duplicates)
            
            verification_results['data_quality'] = quality_checks
            
        except Exception as e:
            self.logger.error(f"Error during verification: {str(e)}")
            verification_results['error'] = str(e)
        finally:
            conn.close()
            
        return verification_results
        
    def test_mcp_performance(self) -> Dict:
        """Test MCP server performance with full dataset"""
        self.logger.info("Testing MCP server performance with full dataset")
        
        performance_results = {}
        
        try:
            # Test 1: Bill listing performance
            start_time = time.time()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT bill_id, bill_type, bill_number, title, sponsor_name
                FROM bills 
                WHERE congress = 118 
                ORDER BY bill_number
                LIMIT 100
            """)
            bills = cursor.fetchall()
            conn.close()
            
            query_time = time.time() - start_time
            performance_results['bill_listing_100'] = {
                'records_returned': len(bills),
                'query_time_seconds': query_time,
                'records_per_second': len(bills) / query_time if query_time > 0 else 0
            }
            
            # Test 2: Full text search performance
            start_time = time.time()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT bill_id, title, official_title
                FROM bills 
                WHERE congress = 118 
                AND (title LIKE '%infrastructure%' OR official_title LIKE '%infrastructure%')
                ORDER BY bill_number
                LIMIT 50
            """)
            search_results = cursor.fetchall()
            conn.close()
            
            search_time = time.time() - start_time
            performance_results['infrastructure_search'] = {
                'records_found': len(search_results),
                'query_time_seconds': search_time,
                'records_per_second': len(search_results) / search_time if search_time > 0 else 0
            }
            
            # Test 3: Content sections retrieval performance
            start_time = time.time()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT bs.bill_id, bs.section_type, bs.header, bs.content
                FROM bill_sections bs
                JOIN bills b ON bs.bill_id = b.bill_id
                WHERE b.congress = 118 AND bs.section_type = 'section'
                ORDER BY bs.bill_id, bs.order_index
                LIMIT 200
            """)
            sections = cursor.fetchall()
            conn.close()
            
            sections_time = time.time() - start_time
            performance_results['sections_retrieval_200'] = {
                'records_returned': len(sections),
                'query_time_seconds': sections_time,
                'records_per_second': len(sections) / sections_time if sections_time > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error during performance testing: {str(e)}")
            performance_results['error'] = str(e)
            
        return performance_results
        
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive verification and performance report"""
        self.logger.info("Generating comprehensive 118th Congress report")
        
        # Data integrity verification
        integrity_results = self.verify_data_integrity()
        
        # Performance testing
        performance_results = self.test_mcp_performance()
        
        # Overall assessment
        overall_assessment = {
            'data_integrity': integrity_results,
            'performance': performance_results,
            'summary': self._generate_summary(integrity_results, performance_results),
            'recommendations': self._generate_recommendations(integrity_results, performance_results)
        }
        
        return overall_assessment
        
    def _generate_summary(self, integrity: Dict, performance: Dict) -> Dict:
        """Generate overall summary assessment"""
        summary = {}
        
        # Data completeness assessment
        total_bills = integrity.get('total_bills', 0)
        completeness = integrity.get('content_completeness', {})
        completeness_pct = completeness.get('completeness_percentage', 0)
        
        if completeness_pct >= 90:
            summary['data_completeness'] = 'EXCELLENT'
        elif completeness_pct >= 75:
            summary['data_completeness'] = 'GOOD'
        elif completeness_pct >= 50:
            summary['data_completeness'] = 'FAIR'
        else:
            summary['data_completeness'] = 'POOR'
            
        # Performance assessment
        avg_query_time = (
            performance.get('bill_listing_100', {}).get('query_time_seconds', 0) +
            performance.get('infrastructure_search', {}).get('query_time_seconds', 0) +
            performance.get('sections_retrieval_200', {}).get('query_time_seconds', 0)
        ) / 3
        
        if avg_query_time <= 0.1:
            summary['performance'] = 'EXCELLENT'
        elif avg_query_time <= 0.5:
            summary['performance'] = 'GOOD'
        elif avg_query_time <= 2.0:
            summary['performance'] = 'FAIR'
        else:
            summary['performance'] = 'POOR'
            
        # Overall readiness
        data_issues = integrity.get('data_quality', {})
        total_issues = (
            data_issues.get('missing_essential_fields', 0) +
            data_issues.get('duplicate_bill_ids', 0)
        )
        
        if summary['data_completeness'] in ['EXCELLENT', 'GOOD'] and summary['performance'] in ['EXCELLENT', 'GOOD'] and total_issues < 10:
            summary['overall_readiness'] = 'PRODUCTION READY'
        elif summary['data_completeness'] in ['GOOD', 'FAIR'] and summary['performance'] in ['GOOD', 'FAIR']:
            summary['overall_readiness'] = 'DEVELOPMENT READY'
        else:
            summary['overall_readiness'] = 'NEEDS IMPROVEMENT'
            
        return summary
        
    def _generate_recommendations(self, integrity: Dict, performance: Dict) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Data quality recommendations
        quality_issues = integrity.get('data_quality', {})
        if quality_issues.get('missing_essential_fields', 0) > 0:
            recommendations.append(f"Fix {quality_issues['missing_essential_fields']} bills with missing essential fields")
            
        if quality_issues.get('duplicate_bill_ids', 0) > 0:
            recommendations.append(f"Resolve {quality_issues['duplicate_bill_ids']} duplicate bill IDs")
            
        # Performance recommendations
        avg_query_time = (
            performance.get('bill_listing_100', {}).get('query_time_seconds', 0) +
            performance.get('infrastructure_search', {}).get('query_time_seconds', 0) +
            performance.get('sections_retrieval_200', {}).get('query_time_seconds', 0)
        ) / 3
        
        if avg_query_time > 1.0:
            recommendations.append("Optimize database indexes for better query performance")
            
        if avg_query_time > 2.0:
            recommendations.append("Consider database query optimization and connection pooling")
            
        # Content recommendations
        completeness = integrity.get('content_completeness', {})
        completeness_pct = completeness.get('completeness_percentage', 0)
        
        if completeness_pct < 80:
            recommendations.append("Improve content extraction to capture more legislative text")
            
        return recommendations
        
    def save_report(self, report: Dict):
        """Save comprehensive report to file"""
        report_file = Path("comprehensive_118th_report.json")
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"Comprehensive report saved to {report_file}")
        except Exception as e:
            self.logger.error(f"Error saving report: {str(e)}")
            
    def print_summary(self, report: Dict):
        """Print formatted summary to console"""
        print("\n" + "="*80)
        print("COMPREHENSIVE 118TH CONGRESS DATA VERIFICATION REPORT")
        print("="*80)
        
        # Data integrity summary
        integrity = report['data_integrity']
        print(f"\n📊 DATA INTEGRITY:")
        print(f"  Total Bills: {integrity.get('total_bills', 0):,}")
        print(f"  Total Sections: {integrity.get('total_sections', 0):,}")
        print(f"  Unique Sponsors: {integrity.get('unique_sponsors', 0):,}")
        
        bill_types = integrity.get('bill_types', {})
        print(f"\n📋 BILL TYPES:")
        for bill_type, count in list(bill_types.items())[:5]:  # Top 5
            print(f"  {bill_type}: {count:,}")
            
        sessions = integrity.get('sessions', {})
        print(f"\n📅 SESSIONS:")
        for session, count in sessions.items():
            print(f"  Session {session}: {count:,} bills")
            
        completeness = integrity.get('content_completeness', {})
        print(f"\n✅ CONTENT COMPLETENESS:")
        print(f"  Bills with Content: {completeness.get('bills_with_content', 0):,}")
        print(f"  Completeness: {completeness.get('completeness_percentage', 0):.1f}%")
        
        # Performance summary
        performance = report['performance']
        print(f"\n⚡ PERFORMANCE:")
        for test_name, results in performance.items():
            if isinstance(results, dict):
                print(f"  {test_name}:")
                print(f"    Records: {results.get('records_returned', 0):,}")
                print(f"    Query Time: {results.get('query_time_seconds', 0):.3f}s")
                print(f"    Rate: {results.get('records_per_second', 0):.1f} records/s")
        
        # Overall assessment
        summary = report['summary']
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"  Data Completeness: {summary.get('data_completeness', 'UNKNOWN')}")
        print(f"  Performance: {summary.get('performance', 'UNKNOWN')}")
        print(f"  Overall Readiness: {summary.get('overall_readiness', 'UNKNOWN')}")
        
        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("="*80)

def main():
    """Main verification and testing entry point"""
    verifier = Comprehensive118thVerifier("data/govinfo_downloads.db")
    
    # Generate comprehensive report
    report = verifier.generate_comprehensive_report()
    
    # Save report
    verifier.save_report(report)
    
    # Print summary
    verifier.print_summary(report)

if __name__ == "__main__":
    main()