# 🎯 Medical Chat API - Quick Reference

## 🔗 Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/medical-chat` | POST | Voice/text medical intake conversation |
| `/api/v1/check-medicine-safety` | POST | Check if medicines are banned/safe |

---

## 💬 Medical Chat Endpoint

### Request (Choose One)

**Option 1: Text Input**
```json
{
  "message": "I have a fever",
  "conversation_history": [],
  "medical_information": null,
  "prescription_data": null
}
```

**Option 2: Audio Input**
```json
{
  "audio_base64": "<base64-encoded-audio>",
  "conversation_history": [],
  "medical_information": null,
  "prescription_data": null
}
```

### Response
```json
{
  "success": true,
  "response": "Thank you for sharing...",
  "audio_response_base64": "<base64-wav-audio>",
  "updated_medical_information": {...},
  "conversation_complete": false,
  "error": null
}
```

---

## 💊 Medicine Safety Check

### Request
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
    }
  ],
  "error": null
}
```

---

## 🚀 Quick Start

### 1. Start Server
```bash
python main.py
```

### 2. Test Text Chat
```bash
curl -X POST "http://localhost:8000/api/v1/medical-chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I have a fever", "conversation_history": [], "medical_information": null, "prescription_data": null}'
```

### 3. Test Medicine Safety
```bash
curl -X POST "http://localhost:8000/api/v1/check-medicine-safety" \
  -H "Content-Type: application/json" \
  -d '{"medicines": ["Paracetamol", "Alprazolam"]}'
```

---

## 🎤 Audio Features

### Input
- **Format**: MP3, WAV, M4A, etc.
- **Encoding**: Base64
- **Field**: `audio_base64`

### Output
- **Format**: WAV
- **Encoding**: Base64
- **Field**: `audio_response_base64`

### Python Example
```python
import base64

# Encode audio for sending
with open('input.mp3', 'rb') as f:
    audio_base64 = base64.b64encode(f.read()).decode('utf-8')

# Decode audio from response
audio_data = base64.b64decode(result['audio_response_base64'])
with open('output.wav', 'wb') as f:
    f.write(audio_data)
```

---

## 📊 Response Fields

### Medical Chat
- `success`: Boolean - Request succeeded
- `response`: String - AI's text response
- `audio_response_base64`: String - AI's audio (WAV)
- `updated_medical_information`: Object - Collected data
  - `reported_disease`: String - Disease/symptoms
  - `medications_provided_by_user`: Array - Medicine names
  - `medication_confirmation`: Boolean - User confirmed
- `conversation_complete`: Boolean - All info collected
- `error`: String - Error message (if failed)

### Medicine Safety
- `success`: Boolean - Request succeeded
- `results`: Array - Safety results
  - `medicine_name`: String - Medicine name
  - `flagged`: Boolean - Banned/restricted/withdrawn
- `error`: String - Error message (if failed)

---

## 🧪 Testing

```bash
# Test audio features
python test_audio_chat.py

# Test all endpoints
python test_new_endpoints.py

# Example workflow
python example_workflow.py
```

---

## 📚 Documentation

- **Audio Features**: `AUDIO_CHAT_DOCUMENTATION.md`
- **All Endpoints**: `NEW_ENDPOINTS_DOCUMENTATION.md`
- **Quick Start**: `QUICKSTART.md`
- **Sample Payloads**: `sample_payloads.json`
- **Interactive Docs**: http://localhost:8000/docs

---

## ⚡ Common Use Cases

### 1. Voice Medical Intake
```python
# User speaks symptoms
response = chat(audio_base64="<audio>")
# AI responds with voice + text
```

### 2. Medicine Verification
```python
# Check if medicines are safe
response = check_safety(["Paracetamol", "Alprazolam"])
# Get flagged medicines
```

### 3. Complete Workflow
```python
# 1. Upload prescription (OCR)
# 2. Verify doctor
# 3. Check medicine safety
# 4. Chat with patient (voice)
# 5. Collect symptoms and confirm medicines
```

---

## ⚠️ Important Notes

- **API Key**: Set `GEMINI_API_KEY` in `.env`
- **Audio Size**: Keep under 10MB
- **Processing Time**: Audio adds 5-10 seconds
- **Rate Limits**: Subject to Gemini API limits
- **Audio Output**: Always WAV format

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Server won't start | Check `GEMINI_API_KEY` in `.env` |
| Audio not working | Verify base64 encoding is correct |
| Slow responses | Audio processing takes 5-10 seconds |
| No audio output | Check `audio_response_base64` field |
| Transcription fails | Ensure audio file is valid format |

---

## 📞 Support

- **Logs**: Check server console for errors
- **Docs**: Visit http://localhost:8000/docs
- **Tests**: Run test scripts to verify setup
