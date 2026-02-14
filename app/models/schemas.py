from pydantic import BaseModel, Field
from typing import List, Optional


class DoctorInfo(BaseModel):
    """Doctor information from prescription."""
    hospital_name: Optional[str] = Field(None, description="Name of the hospital")
    hospital_address: Optional[str] = Field(None, description="Hospital address")
    doctor_name: Optional[str] = Field(None, description="Doctor's name")
    registration_number: Optional[str] = Field(None, description="Doctor's registration number")


class PatientInfo(BaseModel):
    """Patient information from prescription."""
    name: Optional[str] = Field(None, description="Patient's name")
    age: Optional[str] = Field(None, description="Patient's age")
    patient_id: Optional[str] = Field(None, description="Patient ID")
    date: Optional[str] = Field(None, description="Prescription date")


class Medicine(BaseModel):
    """Medicine details from prescription."""
    medicine_name: str = Field(..., description="Name of the medicine")
    dosage: Optional[str] = Field(None, description="Dosage amount (e.g., 500mg, 10ml)")
    dosage_instruction: Optional[str] = Field(None, description="Dosage frequency (e.g., 1-0-1, twice daily)")
    timing: Optional[str] = Field(None, description="AF (After Food) or BF (Before Food)")
    duration: Optional[str] = Field(None, description="Duration of medication (e.g., 5 days, 1 week)")


class PrescriptionData(BaseModel):
    """Complete prescription data extracted from OCR."""
    doctor_info: Optional[DoctorInfo] = None
    patient_info: Optional[PatientInfo] = None
    medicines: List[Medicine] = Field(default_factory=list, description="List of prescribed medicines")


class OCRResponse(BaseModel):
    """Response model for OCR API."""
    success: bool = Field(..., description="Whether OCR was successful")
    data: Optional[PrescriptionData] = Field(None, description="Extracted prescription data")
    error: Optional[str] = Field(None, description="Error message if OCR failed")
    raw_response: Optional[str] = Field(None, description="Raw response from Gemini (for debugging)")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")


class NMCDoctorRecord(BaseModel):
    """Doctor record from NMC registry."""
    serial_no: int = Field(..., description="Serial number in search results")
    registration_year: int = Field(..., description="Year of registration")
    registration_number: str = Field(..., description="Registration number")
    medical_council: str = Field(..., description="Name of medical council")
    doctor_name: str = Field(..., description="Doctor's name from NMC")
    father_or_spouse_name: Optional[str] = Field(None, description="Father or spouse name")
    doctor_id: Optional[str] = Field(None, description="NMC doctor ID")
    name_similarity: Optional[float] = Field(None, description="Name similarity score (0-1)")


class DoctorVerificationResponse(BaseModel):
    """Response for doctor verification API."""
    verified: bool = Field(..., description="Whether the doctor is verified")
    reason: str = Field(..., description="Reason for verification result")
    matches: List[NMCDoctorRecord] = Field(default_factory=list, description="All matching doctors from NMC")
    best_match: Optional[NMCDoctorRecord] = Field(None, description="Best matching doctor record")
    total_matches: int = Field(0, description="Total number of matches found")


class VerifyDoctorRequest(BaseModel):
    """Request model for doctor verification."""
    doctor_name: str = Field(..., description="Doctor's name from prescription")
    registration_number: str = Field(..., description="Doctor's registration number")
    medical_council: Optional[str] = Field(None, description="Medical council name (optional)")


# Medicine Safety Check Schemas
class MedicineFlagResult(BaseModel):
    """Result for individual medicine safety check."""
    medicine_name: str = Field(..., description="Name of the medicine")
    flagged: bool = Field(..., description="True if medicine is banned/restricted/withdrawn")


class MedicineSafetyRequest(BaseModel):
    """Request model for medicine safety check."""
    medicines: List[str] = Field(..., description="List of medicine names to check")


class MedicineSafetyResponse(BaseModel):
    """Response model for medicine safety check."""
    success: bool = Field(..., description="Whether the check was successful")
    results: Optional[List[MedicineFlagResult]] = Field(None, description="Safety check results for each medicine")
    error: Optional[str] = Field(None, description="Error message if check failed")


# Medical Chat Schemas
class ChatMessage(BaseModel):
    """Individual chat message."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class MedicalInformation(BaseModel):
    """Medical information collected during conversation."""
    reported_disease: Optional[str] = Field(None, description="Disease/illness reported by user")
    medications_provided_by_user: Optional[List[str]] = Field(None, description="Medications listed by user")
    medication_confirmation: Optional[bool] = Field(None, description="Whether user confirmed medications")


class MedicalChatRequest(BaseModel):
    """Request model for medical chat."""
    message: str = Field(..., description="User's message")
    conversation_history: List[ChatMessage] = Field(default_factory=list, description="Previous conversation messages")
    medical_information: Optional[MedicalInformation] = Field(None, description="Collected medical information")
    prescription_data: Optional[PrescriptionData] = Field(None, description="Prescription data from OCR (if available)")


class MedicalChatResponse(BaseModel):
    """Response model for medical chat."""
    success: bool = Field(..., description="Whether the chat was successful")
    response: Optional[str] = Field(None, description="AI assistant's response")
    updated_medical_information: Optional[MedicalInformation] = Field(None, description="Updated medical information")
    conversation_complete: bool = Field(False, description="Whether the conversation flow is complete")
    error: Optional[str] = Field(None, description="Error message if chat failed")
