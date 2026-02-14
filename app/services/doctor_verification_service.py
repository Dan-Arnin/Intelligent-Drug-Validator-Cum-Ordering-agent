import requests
import urllib3
import re
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import logging

# Disable SSL warnings for government certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class DoctorVerificationService:
    """Service for verifying doctor credentials against NMC registry."""
    
    NMC_URL = "https://www.nmc.org.in/MCIRest/open/getPaginatedData"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nmc.org.in/information-desk/indian-medical-register/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    def __init__(self, similarity_threshold: float = 0.2):
        """
        Initialize the doctor verification service.
        
        Args:
            similarity_threshold: Minimum similarity score (0-1) for name matching
        """
        self.similarity_threshold = similarity_threshold
    
    def _build_params(self, registration_no: str) -> dict:
        """Build request parameters for NMC API."""
        return {
            "service": "getPaginatedDoctor",
            "draw": "1",
            "start": "0",
            "length": "50",
            "columns[0][data]": "0",
            "columns[0][searchable]": "true",
            "columns[0][orderable]": "true",
            "order[0][column]": "0",
            "order[0][dir]": "asc",
            "registrationNo": registration_no
        }
    
    def _parse_doctor_row(self, row: list) -> dict:
        """
        Convert a raw DataTables row into a clean dictionary.
        
        Args:
            row: Raw row data from NMC API
            
        Returns:
            Dictionary with parsed doctor information
        """
        doctor_id = None
        if row[6]:
            match = re.search(r"openDoctorDetailsnew\('(\d+)'", row[6])
            if match:
                doctor_id = match.group(1)
        
        return {
            "serial_no": row[0],
            "registration_year": row[1],
            "registration_number": row[2],
            "medical_council": row[3],
            "doctor_name": row[4],
            "father_or_spouse_name": row[5],
            "doctor_id": doctor_id
        }
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names using SequenceMatcher.
        
        Args:
            name1: First name to compare
            name2: Second name to compare
            
        Returns:
            Similarity score between 0 and 1
        """
        # Normalize names: lowercase, remove extra spaces, remove common titles
        def normalize(name):
            if not name:
                return ""
            name = name.lower()
            # Remove common titles and punctuation
            titles = ['dr', 'dr.', 'mr', 'mr.', 'mrs', 'mrs.', 'miss', 'ms', 'ms.']
            words = name.split()
            words = [w.strip('.,()') for w in words if w.strip('.,()') not in titles]
            return ' '.join(words)
        
        norm_name1 = normalize(name1)
        norm_name2 = normalize(name2)
        
        # Calculate similarity
        return SequenceMatcher(None, norm_name1, norm_name2).ratio()
    
    def fetch_doctors_by_registration(self, registration_no: str) -> List[Dict]:
        """
        Fetch all doctors with the given registration number from NMC.
        
        Args:
            registration_no: Doctor's registration number
            
        Returns:
            List of doctor records from NMC
        """
        try:
            logger.info(f"Fetching doctors with registration number: {registration_no}")
            
            response = requests.get(
                self.NMC_URL,
                params=self._build_params(registration_no),
                headers=self.HEADERS,
                verify=False,
                timeout=15
            )
            
            logger.info(f"NMC API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"NMC API returned status {response.status_code}")
                return []
            
            # Validate JSON response
            if not response.headers.get("Content-Type", "").startswith("application/json"):
                logger.error("NMC API response is not JSON")
                return []
            
            data = response.json()
            raw_rows = data.get("data", [])
            
            doctors = [self._parse_doctor_row(row) for row in raw_rows]
            logger.info(f"Found {len(doctors)} doctor(s) with registration number {registration_no}")
            
            return doctors
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from NMC API: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_doctors_by_registration: {str(e)}")
            return []
    
    def verify_doctor(
        self, 
        doctor_name: str, 
        registration_no: str,
        medical_council: Optional[str] = None
    ) -> dict:
        """
        Verify if a doctor exists in the NMC registry.
        
        Args:
            doctor_name: Name of the doctor from prescription
            registration_no: Registration number from prescription
            medical_council: Optional medical council name for additional validation
            
        Returns:
            Dictionary with verification results
        """
        if not registration_no:
            return {
                "verified": False,
                "reason": "No registration number provided",
                "matches": [],
                "best_match": None
            }
        
        # Fetch doctors from NMC
        nmc_doctors = self.fetch_doctors_by_registration(registration_no)
        
        if not nmc_doctors:
            return {
                "verified": False,
                "reason": f"No doctors found with registration number {registration_no}",
                "matches": [],
                "best_match": None
            }
        
        # Calculate similarity scores for all matches
        matches_with_scores = []
        for doctor in nmc_doctors:
            similarity = self._calculate_name_similarity(doctor_name, doctor["doctor_name"])
            matches_with_scores.append({
                **doctor,
                "name_similarity": round(similarity, 3)
            })
        
        # Sort by similarity score
        matches_with_scores.sort(key=lambda x: x["name_similarity"], reverse=True)
        
        best_match = matches_with_scores[0] if matches_with_scores else None
        
        # Determine if verified
        verified = False
        reason = ""
        
        if best_match and best_match["name_similarity"] >= self.similarity_threshold:
            verified = True
            reason = f"Doctor verified with {best_match['name_similarity']*100:.1f}% name match"
        elif best_match:
            verified = False
            reason = f"Name similarity too low ({best_match['name_similarity']*100:.1f}%). Possible match found but requires manual verification."
        else:
            verified = False
            reason = "No matching doctor found"
        
        return {
            "verified": verified,
            "reason": reason,
            "matches": matches_with_scores,
            "best_match": best_match,
            "total_matches": len(matches_with_scores)
        }
