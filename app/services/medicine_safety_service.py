import os
import json
import logging
from typing import List, Dict, Any
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a medical regulatory assistant specializing in Indian pharmaceutical regulations.
Your task is to analyze a list of medicines and determine if any of them are:
1. Banned in India.
2. Not for sale (e.g., discontinued, withdrawn).
3. Classified as a Narcotic or Psychotropic substance under the NDPS Act.

Input:
A JSON object containing a list of medicines.

Output:
A JSON list of objects with the following structure:
[
  {
    "medicine_name": "Name from input",
    "flagged": true | false
  }
]

Do not include any other fields or text. The `flagged` field should be true if the medicine is banned, restricted (narcotic/psychotropic), or withdrawn. Otherwise false.
Analyze each medicine carefully using your knowledge base up to late 2024/early 2025.
If a medicine is a combination, check if the specific combination is banned.
"""


class MedicineSafetyService:
    """Service for checking medicine safety using Google Gemini."""
    
    def __init__(self, model_name: str = "gemini-3-pro-preview"):
        """
        Initialize the medicine safety service.
        
        Args:
            model_name: Name of the Gemini model to use
        """
        self.model_name = model_name
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLEAPIKEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLEAPIKEY environment variable must be set")
        
        self.client = genai.Client(api_key=api_key)
        logger.info(f"MedicineSafetyService initialized with model: {model_name}")
    
    def check_medicines(self, medicines: List[str]) -> List[Dict[str, Any]]:
        """
        Check if medicines are safe (not banned/restricted/withdrawn).
        
        Args:
            medicines: List of medicine names to check
            
        Returns:
            List of dictionaries with medicine_name and flagged status
            
        Raises:
            Exception: If the API call fails
        """
        if not medicines:
            return []
        
        # Create the input data structure
        input_data = {
            "data": {
                "medicines": medicines
            }
        }
        
        prompt = f"Analyze the following medicines:\n{json.dumps(medicines, indent=2)}"
        
        try:
            logger.info(f"Checking safety for {len(medicines)} medicines")
            
            response = self.client.models.generate_content(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json"
                ),
                contents=[prompt]
            )
            
            # Parse the JSON response
            result = json.loads(response.text)
            
            logger.info(f"Successfully checked {len(result)} medicines")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
            raise Exception(f"Invalid JSON response from Gemini: {str(e)}")
        
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            raise Exception(f"Medicine safety check failed: {str(e)}")
