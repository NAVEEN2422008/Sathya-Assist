"""
Download authentic PDFs and web pages from Sathyabama portals and ingest into Sathya Assist.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.scrape_and_clean import fetch_and_process_url, load_manifest, save_manifest

TARGETS = [
    {
        "url": "https://www.sathyabama.ac.in/academics/examinations",
        "category": "exams",
        "document_id": "EXAM_COE_OFFICIAL_REGULATIONS_2026",
        "applicable_academic_year": "2026-2027",
        "official_contact_office": "Controller of Examinations (coe@sathyabama.ac.in | 044-24503150)",
        "custom_title": "Sathyabama Controller of Examinations Official Regulations & Grading"
    },
    {
        "url": "https://www.sathyabama.ac.in/campus-life/hostel-facility",
        "category": "hostels",
        "document_id": "HOSTEL_OFFICIAL_RESIDENCE_FACILITIES_2026",
        "applicable_academic_year": "2026-2027",
        "official_contact_office": "Hostel Wardens Office (boyshostel@sathyabama.ac.in / girlshostel@sathyabama.ac.in | 044-24503150)",
        "custom_title": "Sathyabama Hostel Residential Facilities, Amenities and Timings"
    },
    {
        "url": "https://www.sathyabama.ac.in/campus-life/transport-facility",
        "category": "hostels",
        "document_id": "TRANSPORT_OFFICIAL_BUS_SCHEDULE_2026",
        "applicable_academic_year": "2026-2027",
        "official_contact_office": "Transport Office (transport@sathyabama.ac.in | 044-24503150)",
        "custom_title": "Sathyabama Transport Bus Routes & Operational Timings"
    },
    {
        "url": "https://www.sathyabama.ac.in/sites/default/files/2023-07/Hostel%20Rules%20%26%20Regulations.pdf",
        "category": "hostels",
        "document_id": "HOSTEL_OFFICIAL_RULES_AND_REGULATIONS_CIRCULAR",
        "applicable_academic_year": "2026-2027",
        "official_contact_office": "Hostel Administration & Wardens Office (044-24503150)",
        "custom_title": "Official Sathyabama Hostel Rules and Regulations Circular"
    },
    {
        "url": "https://www.sathyabama.ac.in/sites/default/files/2023-04/ACADEMIC%20REGULATION%20UG%20B.E.B.TECH_.pdf",
        "category": "academics",
        "document_id": "ACAD_UG_BE_BTECH_REGULATIONS",
        "applicable_academic_year": "2026-2027",
        "official_contact_office": "Dean Academics & Academic Council",
        "custom_title": "Official Academic Regulations for Undergraduate B.E. / B.Tech Programmes"
    },
    {
        "url": "https://www.sathyabama.ac.in/sites/default/files/2023-04/ACADEMIC%20REGULATION%20PG%20M.E.M.TECH_.pdf",
        "category": "academics",
        "document_id": "ACAD_PG_ME_MTECH_REGULATIONS",
        "applicable_academic_year": "2026-2027",
        "official_contact_office": "Dean Academics & Academic Council",
        "custom_title": "Official Academic Regulations for Postgraduate M.E. / M.Tech Programmes"
    },
    {
        "url": "https://www.sathyabama.ac.in/placements/recruitments",
        "category": "placements",
        "document_id": "PLACE_CDC_OFFICIAL_STATISTICS_POLICY_2026",
        "applicable_academic_year": "2025-2026",
        "official_contact_office": "Centre for Career Guidance and Development (CDC)",
        "custom_title": "Centre for Career Guidance & Development Official Recruitment Statistics & Upgrade Policy"
    },
    {
        "url": "https://feeportal.sathyabama.ac.in/account/Certificate",
        "category": "fees",
        "document_id": "FEE_ONLINE_TRANSCRIPTS_AND_CERTIFICATES_2026",
        "applicable_academic_year": "2026-2027",
        "official_contact_office": "Finance & Controller of Examinations (1800-425-1770)",
        "custom_title": "Official Fee Structure for Transcripts, Grade Sheets and Postal Dispatches"
    }
]

def run_ingestion():
    print("=== Starting Official Document Ingestion ===")
    for item in TARGETS:
        try:
            print(f"\n[Fetching] {item['document_id']} from {item['url']}...")
            fetch_and_process_url(
                url=item["url"],
                category=item["category"],
                document_id=item["document_id"],
                applicable_academic_year=item["applicable_academic_year"],
                official_contact_office=item["official_contact_office"],
                custom_title=item["custom_title"]
            )
        except Exception as e:
            print(f"[Error] Failed to fetch {item['document_id']}: {e}")

if __name__ == "__main__":
    run_ingestion()
