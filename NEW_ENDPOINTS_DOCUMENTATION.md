# New API Endpoints Documentation

## Overview

Two new endpoints have been added to the Medicine Verification Service:

1. **Medicine Safety Check** (`/api/v1/check-medicine-safety`) - Validates medicines against Indian pharmaceutical regulations
2. **Medical Chat** (`/api/v1/medical-chat`) - Conversational AI for collecting symptoms and medication information

---

## 1. Medicine Safety Check Endpoint

### Endpoint
```
POST /api/v1/check-medicine-safety
```

### Description
Checks if medicines are banned, restricted (narcotic/psychotropic under NDPS Act), or withdrawn in India.

### Request Body
```json
{
  "medicines": [
    "Paracetamol",
    "Alprazolam",
    "Codeine"
  ]
}
```

### Response
```json
{
  "success": true,
  "results": [
    {
      "medicine_name": "Paracetamol",
      "flagged": false
    },
    {
      "medicine_name": "Alprazolam",
      "flagged": true
    },
    {
      "medicine_name": "Codeine",
      "flagged": true
    }
  ],
  "error": null
}
```

### Fields

**Request:**
- `medicines` (array of strings, required): List of medicine names to check

**Response:**
- `success` (boolean): Whether the check was successful
- `results` (array): Safety check results for each medicine
  - `medicine_name` (string): Name of the medicine
  - `flagged` (boolean): `true` if banned/restricted/withdrawn, `false` if safe
- `error` (string, nullable): Error message if check failed

### Example Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/check-medicine-safety",
    json={
        "medicines": ["Paracetamol", "Alprazolam", "Phenylpropanolamine"]
    }
)

result = response.json()
for medicine in result["results"]:
    status = "⚠️ FLAGGED" if medicine["flagged"] else "✅ SAFE"
    print(f"{medicine['medicine_name']}: {status}")
```

### Use Cases
- Verify prescription medicines before dispensing
- Check if medicines from OCR extraction are safe
- Validate user-reported medications
- Compliance checking for pharmaceutical applications

---

## 2. Medical Chat Endpoint

### Endpoint
```
POST /api/v1/medical-chat
```

### Description
Conversational AI assistant that follows a structured flow to collect:
1. Disease/illness and symptoms
2. Prescribed medicines
3. Confirmation of medicine list

The AI speaks naturally, adapts to the user's language, and does NOT provide medical advice.

### Request Body
```json
{
  "message": "I have a fever and headache",
  "conversation_history": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "assistant",
      "content": "Hello, I'm here to help collect information..."
    }
  ],
  "medical_information": {
    "reported_disease": null,
    "medications_provided_by_user": null,
    "medication_confirmation": null
  },
  "prescription_data": null
}
```

### Response
```json
{
  "success": true,
  "response": "Thank you for sharing that. Now, please list all the medicines you have been prescribed.",
  "updated_medical_information": {
    "reported_disease": "fever and headache",
    "medications_provided_by_user": null,
    "medication_confirmation": null
  },
  "conversation_complete": false,
  "error": null
}
```

### Fields

**Request:**
- `message` (string, required): User's current message
- `conversation_history` (array): Previous conversation messages
  - `role` (string): Either "user" or "assistant"
  - `content` (string): Message content
- `medical_information` (object, optional): Previously collected information
  - `reported_disease` (string, nullable): Disease/symptoms reported
  - `medications_provided_by_user` (array, nullable): List of medicines
  - `medication_confirmation` (boolean, nullable): User confirmation
- `prescription_data` (object, optional): OCR-extracted prescription data

**Response:**
- `success` (boolean): Whether the chat was successful
- `response` (string): AI assistant's reply
- `updated_medical_information` (object): Updated collected information
- `conversation_complete` (boolean): `true` when all information is collected
- `error` (string, nullable): Error message if chat failed

### Conversation Flow

The AI follows this structured flow:

1. **Opening**: Greets user and asks about disease/symptoms
2. **Collect Disease**: Records the illness and symptoms
3. **Collect Medicines**: Asks for prescribed medicines
4. **Confirmation**: Repeats medicines back and asks for confirmation
5. **Closing**: Thanks user and ends conversation

### Example Usage

```python
import requests

# Start conversation
conversation = []
medical_info = {
    "reported_disease": None,
    "medications_provided_by_user": None,
    "medication_confirmation": None
}

def chat(message):
    global conversation, medical_info
    
    response = requests.post(
        "http://localhost:8000/api/v1/medical-chat",
        json={
            "message": message,
            "conversation_history": conversation,
            "medical_information": medical_info,
            "prescription_data": None
        }
    )
    
    result = response.json()
    
    # Update conversation history
    conversation.append({"role": "user", "content": message})
    conversation.append({"role": "assistant", "content": result["response"]})
    
    # Update medical information
    if result["updated_medical_information"]:
        medical_info = result["updated_medical_information"]
    
    print(f"Assistant: {result['response']}")
    print(f"Complete: {result['conversation_complete']}\n")
    
    return result

# Example conversation
chat("Hello")
chat("I have a fever and cough for 3 days")
chat("The doctor prescribed Paracetamol and Azithromycin")
chat("Yes, that's correct")
```

### Integration with Prescription OCR

You can pass prescription data from the OCR endpoint to provide context:

```python
# First, extract prescription
ocr_response = requests.post(
    "http://localhost:8000/api/v1/upload-prescription",
    files={"file": open("prescription.pdf", "rb")}
)

prescription_data = ocr_response.json()["data"]

# Then use in chat
chat_response = requests.post(
    "http://localhost:8000/api/v1/medical-chat",
    json={
        "message": "I have the symptoms mentioned in the prescription",
        "conversation_history": [],
        "medical_information": None,
        "prescription_data": prescription_data  # Include OCR data
    }
)
```

### Multi-language Support

The AI automatically detects and responds in the user's language:

```python
# User speaks in Hindi
chat("Namaste, mujhe bukhar hai")
# AI responds in Hindi

# User switches to English
chat("Actually, let me speak in English")
# AI switches to English
```

---

## Complete Workflow Example

Here's a complete workflow combining all endpoints:

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Step 1: Upload prescription
with open("prescription.pdf", "rb") as f:
    ocr_response = requests.post(
        f"{BASE_URL}/upload-prescription",
        files={"file": f}
    )

prescription = ocr_response.json()["data"]
print(f"Extracted {len(prescription['medicines'])} medicines")

# Step 2: Verify doctor
doctor_response = requests.post(
    f"{BASE_URL}/verify-doctor",
    json={
        "doctor_name": prescription["doctor_info"]["doctor_name"],
        "registration_number": prescription["doctor_info"]["registration_number"]
    }
)

verified = doctor_response.json()["verified"]
print(f"Doctor verified: {verified}")

# Step 3: Check medicine safety
medicine_names = [m["medicine_name"] for m in prescription["medicines"]]
safety_response = requests.post(
    f"{BASE_URL}/check-medicine-safety",
    json={"medicines": medicine_names}
)

flagged_medicines = [
    m["medicine_name"] 
    for m in safety_response.json()["results"] 
    if m["flagged"]
]

if flagged_medicines:
    print(f"⚠️ Warning: Flagged medicines: {flagged_medicines}")
else:
    print("✅ All medicines are safe")

# Step 4: Chat with patient to verify symptoms
chat_response = requests.post(
    f"{BASE_URL}/medical-chat",
    json={
        "message": "Hello, I have this prescription",
        "conversation_history": [],
        "medical_information": None,
        "prescription_data": prescription
    }
)

print(f"AI: {chat_response.json()['response']}")
```

---

## Testing

Run the test script to verify all endpoints:

```bash
python test_new_endpoints.py
```

Or test manually using the interactive API docs:

```
http://localhost:8000/docs
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "results": null,  // or response: null for chat
  "error": "Error message describing what went wrong"
}
```

Common errors:
- Missing API key: "GEMINI_API_KEY environment variable must be set"
- Empty input: "No medicines provided" or empty message
- API failures: "Medicine safety check failed: [details]"

---

## Notes

1. **API Key Required**: Both endpoints require `GEMINI_API_KEY` in your `.env` file
2. **Rate Limits**: Subject to Google Gemini API rate limits
3. **Language Support**: Medical chat supports multiple languages automatically
4. **No Medical Advice**: The chat assistant only collects information, never provides medical advice
5. **Conversation State**: Client must maintain conversation history and medical information between requests
