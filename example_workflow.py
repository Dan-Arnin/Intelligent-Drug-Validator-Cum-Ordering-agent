"""
Example: Complete medical verification workflow
This demonstrates how to use the medical chat and medicine safety endpoints together.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


class MedicalAssistant:
    """Helper class to manage medical chat conversations."""
    
    def __init__(self):
        self.conversation_history = []
        self.medical_information = {
            "reported_disease": None,
            "medications_provided_by_user": None,
            "medication_confirmation": None
        }
        self.prescription_data = None
    
    def chat(self, message):
        """Send a message and get response."""
        response = requests.post(
            f"{BASE_URL}/medical-chat",
            json={
                "message": message,
                "conversation_history": self.conversation_history,
                "medical_information": self.medical_information,
                "prescription_data": self.prescription_data
            }
        )
        
        result = response.json()
        
        if result["success"]:
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": result["response"]
            })
            
            # Update medical information
            if result["updated_medical_information"]:
                self.medical_information = result["updated_medical_information"]
            
            return result
        else:
            raise Exception(result.get("error", "Chat failed"))
    
    def check_medicine_safety(self):
        """Check if collected medicines are safe."""
        medicines = self.medical_information.get("medications_provided_by_user")
        
        if not medicines:
            return None
        
        response = requests.post(
            f"{BASE_URL}/check-medicine-safety",
            json={"medicines": medicines}
        )
        
        return response.json()


def example_conversation():
    """Example conversation flow."""
    print("="*70)
    print("MEDICAL VERIFICATION ASSISTANT - EXAMPLE WORKFLOW")
    print("="*70)
    
    assistant = MedicalAssistant()
    
    # Conversation flow
    conversations = [
        "Hello",
        "I have been suffering from high fever and body pain for the last 2 days",
        "The doctor prescribed Paracetamol 500mg, Ibuprofen 400mg, and Alprazolam",
        "Yes, that's correct"
    ]
    
    for user_message in conversations:
        print(f"\n👤 User: {user_message}")
        
        result = assistant.chat(user_message)
        
        print(f"🤖 Assistant: {result['response']}")
        
        if result.get("updated_medical_information"):
            print(f"\n📋 Collected Information:")
            info = result["updated_medical_information"]
            if info.get("reported_disease"):
                print(f"   Disease: {info['reported_disease']}")
            if info.get("medications_provided_by_user"):
                print(f"   Medicines: {', '.join(info['medications_provided_by_user'])}")
            if info.get("medication_confirmation") is not None:
                print(f"   Confirmed: {info['medication_confirmation']}")
        
        if result.get("conversation_complete"):
            print("\n✅ Conversation Complete!")
            break
    
    # Check medicine safety
    print("\n" + "="*70)
    print("CHECKING MEDICINE SAFETY")
    print("="*70)
    
    safety_result = assistant.check_medicine_safety()
    
    if safety_result and safety_result["success"]:
        print("\n🔍 Safety Check Results:\n")
        
        safe_medicines = []
        flagged_medicines = []
        
        for medicine in safety_result["results"]:
            if medicine["flagged"]:
                flagged_medicines.append(medicine["medicine_name"])
                print(f"   ⚠️  {medicine['medicine_name']} - FLAGGED (Banned/Restricted/Withdrawn)")
            else:
                safe_medicines.append(medicine["medicine_name"])
                print(f"   ✅ {medicine['medicine_name']} - SAFE")
        
        print(f"\n📊 Summary:")
        print(f"   Total medicines: {len(safety_result['results'])}")
        print(f"   Safe: {len(safe_medicines)}")
        print(f"   Flagged: {len(flagged_medicines)}")
        
        if flagged_medicines:
            print(f"\n⚠️  WARNING: The following medicines are flagged:")
            for med in flagged_medicines:
                print(f"   - {med}")
            print(f"\n   These medicines may be banned, restricted under NDPS Act,")
            print(f"   or withdrawn from sale in India. Please verify with a licensed")
            print(f"   pharmacist or medical professional.")
    
    print("\n" + "="*70)
    print("WORKFLOW COMPLETE")
    print("="*70)


def example_with_prescription_ocr():
    """Example showing integration with prescription OCR."""
    print("\n" + "="*70)
    print("EXAMPLE: INTEGRATION WITH PRESCRIPTION OCR")
    print("="*70)
    
    # Simulate prescription data (normally from OCR endpoint)
    prescription_data = {
        "doctor_info": {
            "doctor_name": "Dr. Rajesh Kumar",
            "registration_number": "12345",
            "hospital_name": "City Hospital"
        },
        "patient_info": {
            "name": "John Doe",
            "age": "35"
        },
        "medicines": [
            {"medicine_name": "Paracetamol", "dosage": "500mg"},
            {"medicine_name": "Amoxicillin", "dosage": "250mg"}
        ]
    }
    
    assistant = MedicalAssistant()
    assistant.prescription_data = prescription_data
    
    print("\n📄 Prescription Data Loaded:")
    print(f"   Doctor: {prescription_data['doctor_info']['doctor_name']}")
    print(f"   Patient: {prescription_data['patient_info']['name']}")
    print(f"   Medicines: {', '.join([m['medicine_name'] for m in prescription_data['medicines']])}")
    
    print("\n👤 User: Hello, I have this prescription")
    result = assistant.chat("Hello, I have this prescription")
    print(f"🤖 Assistant: {result['response']}")
    
    print("\n💡 The AI now has access to the prescription data and can use it")
    print("   to verify the information provided by the patient.")


if __name__ == "__main__":
    try:
        # Run main conversation example
        example_conversation()
        
        # Run OCR integration example
        example_with_prescription_ocr()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("Make sure the server is running on http://localhost:8000")
        print("\nStart the server with: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
