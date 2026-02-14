from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.models.schemas import (
    OCRResponse, PrescriptionData, DoctorInfo, PatientInfo, Medicine,
    DoctorVerificationResponse, VerifyDoctorRequest, NMCDoctorRecord,
    MedicineSafetyRequest, MedicineSafetyResponse, MedicineFlagResult,
    MedicalChatRequest, MedicalChatResponse, ChatMessage, MedicalInformation
)
from app.services.gemini_service import GeminiOCRService
from app.services.doctor_verification_service import DoctorVerificationService
from app.services.medicine_safety_service import MedicineSafetyService
from app.services.medical_chat_service import MedicalChatService
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["prescription"])

# Initialize services
gemini_service = GeminiOCRService()
doctor_verification_service = DoctorVerificationService(similarity_threshold=0.2)
medicine_safety_service = MedicineSafetyService()
medical_chat_service = MedicalChatService()



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
            # Key mapping: Gemini may return various key formats
            medicine_key_map = {
                "medicine name": "medicine_name",
                "medicine_name": "medicine_name",
                "medicinename": "medicine_name",
                "name": "medicine_name",
                "dosage": "dosage",
                "dosage amount": "dosage",
                "dosage_instruction": "dosage_instruction",
                "dosage instruction": "dosage_instruction",
                "dosageinstruction": "dosage_instruction",
                "frequency": "dosage_instruction",
                "timing": "timing",
                "duration": "duration",
            }
            
            if "medicines" in extracted_data:
                for med in extracted_data["medicines"]:
                    # Normalize keys: "Medicine Name" -> "medicine_name"
                    normalized = {}
                    for key, value in med.items():
                        normalized_key = medicine_key_map.get(key.lower().strip(), key.lower().replace(" ", "_"))
                        normalized[normalized_key] = value
                    
                    # Ensure medicine_name exists (required field)
                    if "medicine_name" not in normalized:
                        # Try to find any key that looks like a name
                        for k, v in normalized.items():
                            if "name" in k and v:
                                normalized["medicine_name"] = v
                                break
                    
                    if "medicine_name" in normalized and normalized["medicine_name"]:
                        medicines.append(Medicine(**{k: v for k, v in normalized.items() if k in Medicine.model_fields}))
            
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


@router.post("/check-medicine-safety", response_model=MedicineSafetyResponse)
async def check_medicine_safety(request: MedicineSafetyRequest):
    """
    Check if medicines are safe (not banned, restricted, or withdrawn in India).
    
    Args:
        request: List of medicine names to check
    
    Returns:
        MedicineSafetyResponse with safety status for each medicine
    """
    try:
        logger.info(f"Checking safety for {len(request.medicines)} medicines")
        
        if not request.medicines:
            return MedicineSafetyResponse(
                success=False,
                results=None,
                error="No medicines provided"
            )
        
        # Check medicines using the safety service
        results = medicine_safety_service.check_medicines(request.medicines)
        
        # Convert to response model
        flag_results = [MedicineFlagResult(**result) for result in results]
        
        logger.info(f"Safety check complete. Flagged: {sum(1 for r in flag_results if r.flagged)}/{len(flag_results)}")
        
        return MedicineSafetyResponse(
            success=True,
            results=flag_results,
            error=None
        )
    
    except Exception as e:
        logger.error(f"Error checking medicine safety: {str(e)}", exc_info=True)
        return MedicineSafetyResponse(
            success=False,
            results=None,
            error=f"Error checking medicine safety: {str(e)}"
        )


@router.post("/medical-chat", response_model=MedicalChatResponse)
async def medical_chat(request: MedicalChatRequest):
    """
    Chat with AI assistant to collect medical symptoms and medication information.
    
    This endpoint follows a structured conversation flow to:
    1. Collect disease/illness and symptoms
    2. Collect prescribed medicines
    3. Confirm the medicine list
    
    Supports both text and audio input/output:
    - Send text via 'message' field
    - Send audio via 'audio_base64' field (base64 encoded audio)
    - Receive text response in 'response' field
    - Receive audio response in 'audio_response_base64' field (base64 encoded WAV)
    
    Args:
        request: User message (text or audio), conversation history, and collected medical information
    
    Returns:
        MedicalChatResponse with AI response (text and audio) and updated medical information
    """
    try:
        # Log request details for debugging
        logger.info("="*60)
        logger.info("MEDICAL CHAT REQUEST RECEIVED")
        logger.info(f"  message: {str(request.message)[:10] if request.message else 'None'}...")
        logger.info(f"  audio_base64: {str(request.audio_base64)[:10] if request.audio_base64 else 'None'}...")
        logger.info(f"  conversation_history: {len(request.conversation_history)} messages")
        logger.info(f"  medical_information: {request.medical_information}")
        logger.info(f"  prescription_data: {'Present' if request.prescription_data else 'None'}")
        logger.info("="*60)
        
        # Determine if audio or text input
        input_type = "audio" if request.audio_base64 else "text"
        log_message = f"audio input ({len(request.audio_base64) if request.audio_base64 else 0} bytes)" if input_type == "audio" else f"text: {request.message[:50] if request.message else 'empty'}..."
        logger.info(f"Processing medical chat - {log_message}")
        
        # Validate input
        if not request.message and not request.audio_base64:
            return MedicalChatResponse(
                success=False,
                response=None,
                audio_response_base64=None,
                updated_medical_information=None,
                conversation_complete=False,
                error="Either 'message' or 'audio_base64' must be provided"
            )
        
        # Normalize conversation history from ANY format to {role, content}
        conversation_history = []
        for msg in (request.conversation_history or []):
            if isinstance(msg, str):
                # Handle string format: "User: Hi" or "Assistant: Hello..."
                msg_lower = msg.strip()
                if msg_lower.lower().startswith("user:"):
                    conversation_history.append({"role": "user", "content": msg_lower[5:].strip()})
                elif msg_lower.lower().startswith("assistant:"):
                    conversation_history.append({"role": "assistant", "content": msg_lower[10:].strip()})
                elif msg_lower.lower().startswith("bot:"):
                    conversation_history.append({"role": "assistant", "content": msg_lower[4:].strip()})
                else:
                    # Unknown format string, treat as user message
                    conversation_history.append({"role": "user", "content": msg_lower})
            
            elif isinstance(msg, dict):
                # Handle {role: "...", content: "..."} format
                role = msg.get("role") or msg.get("sender") or None
                content = msg.get("content") or msg.get("text") or msg.get("message") or None
                
                if role and content:
                    conversation_history.append({"role": role, "content": content})
                
                # Handle {user: "...", bot: "..."} format (each key = separate message)
                if "user" in msg and msg["user"]:
                    conversation_history.append({"role": "user", "content": msg["user"]})
                if "bot" in msg and msg["bot"]:
                    conversation_history.append({"role": "assistant", "content": msg["bot"]})
            
            else:
                # Pydantic model or other object
                conversation_history.append({"role": getattr(msg, 'role', 'user'), "content": getattr(msg, 'content', str(msg))})
        
        logger.info(f"  Normalized conversation_history: {len(conversation_history)} messages")
        
        # Medical information is now a raw dict, pass directly
        medical_info = request.medical_information
        
        # Prescription data is now a raw dict, pass directly
        prescription_data = request.prescription_data
        
        # Process the chat with audio support
        result = medical_chat_service.chat(
            user_message=request.message,
            audio_base64=request.audio_base64,
            conversation_history=conversation_history,
            medical_information=medical_info,
            prescription_data=prescription_data,
            return_audio=True  # Always generate audio response
        )
        
        # Get updated medical information (already a dict)
        updated_medical_info = result.get("updated_medical_information")
        
        logger.info(f"Chat response generated. Complete: {result.get('conversation_complete', False)}")
        
        return MedicalChatResponse(
            success=True,
            response=result.get("response"),
            audio_response_base64=result.get("audio_response_base64"),
            updated_medical_information=updated_medical_info,
            conversation_complete=result.get("conversation_complete", False),
            error=None
        )
    
    except Exception as e:
        logger.error(f"Error in medical chat: {str(e)}", exc_info=True)
        return MedicalChatResponse(
            success=False,
            response=None,
            audio_response_base64=None,
            updated_medical_information=None,
            conversation_complete=False,
            error=f"Error in medical chat: {str(e)}"
        )


