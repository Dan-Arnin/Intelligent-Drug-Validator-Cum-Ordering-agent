# Medicine Verification Service - Quick Start

## 🚀 New Features Added

Two powerful new endpoints have been added to enhance the medicine verification workflow:

### 1. 💊 Medicine Safety Check
**Endpoint:** `POST /api/v1/check-medicine-safety`

Validates medicines against Indian pharmaceutical regulations to check if they are:
- Banned in India
- Withdrawn from sale
- Classified as Narcotic/Psychotropic under NDPS Act

### 2. 💬 Medical Chat Assistant
**Endpoint:** `POST /api/v1/medical-chat`

Conversational AI that collects:
- Patient symptoms and disease information
- Prescribed medicines
- Confirmation of medication list

The AI speaks naturally, adapts to user's language, and follows a structured conversation flow.

---

## 📋 All Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/upload-prescription` | POST | Extract prescription data from PDF/image |
| `/api/v1/verify-doctor` | POST | Verify doctor credentials against NMC registry |
| `/api/v1/check-medicine-safety` | POST | Check if medicines are safe/banned |
| `/api/v1/medical-chat` | POST | Chat with AI to collect medical information |
| `/api/v1/health` | GET | Health check |

---

## 🏃 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
Create a `.env` file:
```env
GEMINI_API_KEY=your_api_key_here
```

### 3. Start Server
```bash
python main.py
```

Server runs on: `http://localhost:8000`

### 4. View API Documentation
Open in browser: `http://localhost:8000/docs`

---

## 🧪 Testing

### Run All Tests
```bash
python test_new_endpoints.py
```

### Run Example Workflow
```bash
python example_workflow.py
```

This demonstrates:
- Complete conversation flow
- Medicine safety checking
- Integration with prescription OCR

---

## 📖 Documentation

- **Detailed API Docs:** [NEW_ENDPOINTS_DOCUMENTATION.md](NEW_ENDPOINTS_DOCUMENTATION.md)
- **Interactive Docs:** http://localhost:8000/docs (when server is running)
- **Example Code:** [example_workflow.py](example_workflow.py)

---

## 💡 Example Usage

### Medicine Safety Check
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/check-medicine-safety",
    json={"medicines": ["Paracetamol", "Alprazolam", "Codeine"]}
)

for medicine in response.json()["results"]:
    status = "⚠️ FLAGGED" if medicine["flagged"] else "✅ SAFE"
    print(f"{medicine['medicine_name']}: {status}")
```

### Medical Chat
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/medical-chat",
    json={
        "message": "I have fever and headache",
        "conversation_history": [],
        "medical_information": None,
        "prescription_data": None
    }
)

print(response.json()["response"])
```

---

## 🔗 Complete Workflow

```python
# 1. Upload prescription
ocr_result = upload_prescription("prescription.pdf")

# 2. Verify doctor
doctor_verified = verify_doctor(
    ocr_result["doctor_info"]["doctor_name"],
    ocr_result["doctor_info"]["registration_number"]
)

# 3. Check medicine safety
medicine_names = [m["medicine_name"] for m in ocr_result["medicines"]]
safety_result = check_medicine_safety(medicine_names)

# 4. Chat with patient
chat_result = medical_chat(
    message="Hello",
    prescription_data=ocr_result
)
```

---

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **AI Model:** Google Gemini 2.0 Flash
- **OCR:** Google Gemini Vision
- **Doctor Verification:** NMC Registry Integration
- **Medicine Safety:** AI-powered regulatory checking

---

## 📝 Notes

- Both new endpoints require `GEMINI_API_KEY` environment variable
- Medical chat supports multiple languages automatically
- Medicine safety checks are based on Indian pharmaceutical regulations
- The chat assistant does NOT provide medical advice, only collects information

---

## 🆘 Troubleshooting

### Server won't start
- Check if `GEMINI_API_KEY` is set in `.env`
- Ensure port 8000 is not in use

### API errors
- Verify API key is valid
- Check internet connection (required for Gemini API)
- Review logs for detailed error messages

### Test failures
- Ensure server is running: `python main.py`
- Check if all dependencies are installed: `pip install -r requirements.txt`

---

## 📞 Support

For detailed documentation, see [NEW_ENDPOINTS_DOCUMENTATION.md](NEW_ENDPOINTS_DOCUMENTATION.md)

For API reference, visit: http://localhost:8000/docs
