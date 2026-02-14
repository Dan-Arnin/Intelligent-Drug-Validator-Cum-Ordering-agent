import os
import base64
import io
from typing import Optional
from PIL import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
from google import genai
from google.genai import types


class GeminiOCRService:
    """Service for performing OCR on medical prescriptions using Google Gemini."""
    
    def __init__(self):
        """Initialize the Gemini client."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3-pro-preview"
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def _pdf_to_images(self, pdf_bytes: bytes) -> list[Image.Image]:
        """Convert PDF bytes to list of PIL Images."""
        return convert_from_bytes(pdf_bytes)
    
    def extract_prescription_data(self, file_bytes: bytes, mime_type: str) -> dict:
        """
        Extract prescription data from uploaded file using Gemini OCR.
        
        Args:
            file_bytes: Raw bytes of the uploaded file
            mime_type: MIME type of the file (e.g., 'image/jpeg', 'application/pdf')
        
        Returns:
            Dictionary containing extracted prescription data
        """
        # Handle PDF files - convert to images first
        if mime_type == "application/pdf":
            images = self._pdf_to_images(file_bytes)
            # For now, process only the first page
            # You can extend this to process multiple pages
            if not images:
                raise ValueError("PDF file contains no pages")
            
            image = images[0]
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            file_bytes = buffered.getvalue()
            mime_type = "image/jpeg"
        
        # Handle image files
        elif mime_type.startswith("image/"):
            # Convert to JPEG if needed
            if mime_type not in ["image/jpeg", "image/jpg"]:
                image = Image.open(io.BytesIO(file_bytes))
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                file_bytes = buffered.getvalue()
                mime_type = "image/jpeg"
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")
        
        # Prepare the prompt for Gemini
        prompt = """Extract the details of the patient, doctor info and all the medicines prescribed here. 

Make a JSON output with the following 3 keys with data within them:

1. "doctor_info": Include Hospital Name and Address, Doctor Name, Registration Number
2. "patient_info": Include Name, Age, Patient ID, Date
3. "medicines": An array of medicine objects, each containing:
   - Medicine Name
   - Dosage (e.g., "500mg", "10ml")
   - Dosage Instruction (e.g., "1-0-1", "2 times daily")
   - Timing: "AF" (After Food) or "BF" (Before Food)
   - Duration (e.g., "5 days", "1 week")

Return ONLY valid JSON, no additional text or markdown formatting."""
        
        # Create content for Gemini
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        mime_type=mime_type,
                        data=file_bytes,
                    ),
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        # Configure tools (Google Search for medicine verification)
        tools = [
            types.Tool(googleSearch=types.GoogleSearch()),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_level="HIGH",
            ),
            tools=tools,
        )
        
        # Generate content
        response_text = ""
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response_text += chunk.text
        
        # Parse the response
        import json
        try:
            # Try to extract JSON from the response
            # Sometimes the model might wrap JSON in markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            extracted_data = json.loads(response_text)
            return extracted_data
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return the raw text
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response_text,
                "parse_error": str(e)
            }
