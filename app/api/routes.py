from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.models.schemas import (
    OCRResponse, PrescriptionData, DoctorInfo, PatientInfo, Medicine,
    DoctorVerificationResponse, VerifyDoctorRequest, NMCDoctorRecord
)
from app.services.gemini_service import GeminiOCRService
from app.services.doctor_verification_service import DoctorVerificationService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["prescription"])

# Initialize services
gemini_service = GeminiOCRService()
doctor_verification_service = DoctorVerificationService(similarity_threshold=0.2)


@router.post("/upload-prescription", response_model=OCRResponse)
async def upload_prescription(file: UploadFile = File(...)):
    """
    Upload a prescription document (PDF or image) and extract medicine details.
    
    Args:
        file: Uploaded file (PDF, JPG, JPEG, PNG)
    
    Returns:
        OCRResponse containing extracted prescription data
    """
    # Validate file type
    allowed_types = [
        "application/pdf",
        "image/jpeg",
        "image/jpg",
        "image/png",
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: PDF, JPEG, JPG, PNG. Got: {file.content_type}"
        )
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    file_bytes = await file.read()
    
    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: 10MB. Got: {len(file_bytes) / (1024*1024):.2f}MB"
        )
    
    try:
        logger.info(f"Processing file: {file.filename}, type: {file.content_type}, size: {len(file_bytes)} bytes")
        
        # Extract prescription data using Gemini
        extracted_data = gemini_service.extract_prescription_data(
            file_bytes=file_bytes,
            mime_type=file.content_type
        )
        
        # Check if there was an error in extraction
        if "error" in extracted_data:
            return OCRResponse(
                success=False,
                data=None,
                error=extracted_data.get("error"),
                raw_response=extracted_data.get("raw_response")
            )
        
        # Parse the extracted data into structured models
        try:
            # Parse doctor info
            doctor_info = None
            if "doctor_info" in extracted_data:
                doctor_info = DoctorInfo(**extracted_data["doctor_info"])
            
            # Parse patient info
            patient_info = None
            if "patient_info" in extracted_data:
                patient_info = PatientInfo(**extracted_data["patient_info"])
            
            # Parse medicines
            medicines = []
            if "medicines" in extracted_data:
                for med in extracted_data["medicines"]:
                    medicines.append(Medicine(**med))
            
            prescription_data = PrescriptionData(
                doctor_info=doctor_info,
                patient_info=patient_info,
                medicines=medicines
            )
            
            logger.info(f"Successfully extracted {len(medicines)} medicines from prescription")
            
            return OCRResponse(
                success=True,
                data=prescription_data,
                error=None
            )
        
        except Exception as e:
            logger.error(f"Error parsing extracted data: {str(e)}")
            return OCRResponse(
                success=False,
                data=None,
                error=f"Error parsing extracted data: {str(e)}",
                raw_response=str(extracted_data)
            )
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )




@router.post("/verify-doctor", response_model=DoctorVerificationResponse)
async def verify_doctor(request: VerifyDoctorRequest):
    """
    Verify a doctor's credentials against the National Medical Council (NMC) registry.
    
    Args:
        request: Doctor verification request with name and registration number
    
    Returns:
        DoctorVerificationResponse with verification status and matching records
    """
    try:
        logger.info(f"Verifying doctor: {request.doctor_name}, Reg No: {request.registration_number}")
        
        # Verify doctor using the verification service
        verification_result = doctor_verification_service.verify_doctor(
            doctor_name=request.doctor_name,
            registration_no=request.registration_number,
            medical_council=request.medical_council
        )
        
        # Convert to response model
        matches = [NMCDoctorRecord(**match) for match in verification_result["matches"]]
        best_match = None
        if verification_result["best_match"]:
            best_match = NMCDoctorRecord(**verification_result["best_match"])
        
        response = DoctorVerificationResponse(
            verified=verification_result["verified"],
            reason=verification_result["reason"],
            matches=matches,
            best_match=best_match,
            total_matches=verification_result["total_matches"]
        )
        
        logger.info(f"Verification result: {response.verified}, Matches: {response.total_matches}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error verifying doctor: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error verifying doctor: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Medicine Verification Service is running"
    }
