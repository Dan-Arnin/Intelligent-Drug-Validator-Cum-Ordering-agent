# Medicine Verification Service

A FastAPI-based service for extracting prescription details from medical documents using Google Gemini 3 OCR.

## Features

- 📄 **Multi-format Support**: Upload PDFs, JPG, JPEG, or PNG prescription images
- 🤖 **AI-Powered OCR**: Uses Google Gemini 3 Pro for intelligent text extraction
- 📊 **Structured Data**: Extracts doctor info, patient details, and medicine information
- 🔍 **Medicine Verification**: Leverages Google Search for medicine validation
- ⚡ **Fast & Scalable**: Built with FastAPI for high performance

## Extracted Information

The service extracts:

### Doctor Information
- Hospital Name and Address
- Doctor Name
- Registration Number

### Patient Information
- Patient Name
- Age
- Patient ID
- Prescription Date

### Medicine Details
- Medicine Name
- Dosage (e.g., 500mg, 10ml)
- Dosage Instructions (e.g., 1-0-1, twice daily)
- Timing (AF - After Food, BF - Before Food)
- Duration (e.g., 5 days, 1 week)

## Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up environment variables**:
Create a `.env` file with:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

## Running the Service

### Development Mode
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### 1. Upload Prescription
**POST** `/api/v1/upload-prescription`

Upload a prescription document for OCR processing.

**Request**:
- Method: POST
- Content-Type: multipart/form-data
- Body: file (PDF, JPG, JPEG, PNG)
- Max file size: 10MB

**Response**:
```json
{
  "success": true,
  "data": {
    "doctor_info": {
      "hospital_name": "City Hospital",
      "hospital_address": "123 Main St",
      "doctor_name": "Dr. John Smith",
      "registration_number": "MED12345"
    },
    "patient_info": {
      "name": "Jane Doe",
      "age": "35",
      "patient_id": "P12345",
      "date": "2026-02-14"
    },
    "medicines": [
      {
        "medicine_name": "Amoxicillin",
        "dosage": "500mg",
        "dosage_instruction": "1-0-1",
        "timing": "AF",
        "duration": "5 days"
      }
    ]
  },
  "error": null
}
```

### 2. Health Check
**GET** `/api/v1/health`

Check if the service is running.

**Response**:
```json
{
  "status": "healthy",
  "message": "Medicine Verification Service is running"
}
```

## Usage Examples

### Using cURL
```bash
curl -X POST "http://localhost:8000/api/v1/upload-prescription" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@prescription.jpg"
```

### Using Python
```python
import requests

url = "http://localhost:8000/api/v1/upload-prescription"
files = {"file": open("prescription.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### Using JavaScript/Fetch
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/v1/upload-prescription', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models
│   └── services/
│       ├── __init__.py
│       └── gemini_service.py  # Gemini OCR service
├── main.py                     # FastAPI app entry point
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md                   # This file
```

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid file type, file too large)
- `500`: Internal server error

Error response format:
```json
{
  "success": false,
  "data": null,
  "error": "Error message here",
  "raw_response": "Raw Gemini response for debugging"
}
```

## Supported File Types

- **Images**: JPEG, JPG, PNG
- **Documents**: PDF (first page only)

## Limitations

- Maximum file size: 10MB
- PDF processing: Only the first page is processed
- Requires valid GEMINI_API_KEY

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest
```

### Code Formatting
```bash
pip install black
black .
```

## License

MIT License

## Support

For issues or questions, please open an issue on the repository.
