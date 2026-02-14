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
