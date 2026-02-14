# Audio-Enabled Medical Chat API

## Overview

The medical chat endpoint now supports **voice conversations**! You can:
- 🎤 Send audio messages (base64 encoded)
- 🔊 Receive audio responses (base64 encoded WAV)
- 💬 Continue using text if preferred
- 🔄 Mix text and audio in the same conversation

---

## Endpoint

```
POST /api/v1/medical-chat
```

---

## Audio Features

### Input Options
1. **Text Input**: Send `message` field with text
2. **Audio Input**: Send `audio_base64` field with base64-encoded audio (MP3, WAV, etc.)

### Output
- **Text Response**: Always returned in `response` field
- **Audio Response**: Always returned in `audio_response_base64` field (base64-encoded WAV)

---

## Request Examples

### 1. Text Input (Get Text + Audio Response)

```json
{
  "message": "Hello, I have a fever",
  "conversation_history": [],
  "medical_information": null,
  "prescription_data": null
}
```

### 2. Audio Input (Get Text + Audio Response)

```json
{
  "audio_base64": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA...",
  "conversation_history": [],
  "medical_information": null,
  "prescription_data": null
}
```

### 3. Mixed Conversation

You can mix text and audio in the same conversation:

```json
{
  "message": "The doctor prescribed Paracetamol",
  "conversation_history": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "assistant",
      "content": "Hello, I'm here to help..."
    }
  ],
  "medical_information": {
    "reported_disease": "fever and headache",
    "medications_provided_by_user": null,
    "medication_confirmation": null
  },
  "prescription_data": null
}
```

---

## Response Format

```json
{
  "success": true,
  "response": "Thank you for sharing that. Now, please list all the medicines...",
  "audio_response_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQAAAAA=",
  "updated_medical_information": {
    "reported_disease": "fever and headache",
    "medications_provided_by_user": null,
    "medication_confirmation": null
  },
  "conversation_complete": false,
  "error": null
}
```

### Response Fields

- `success` (boolean): Whether the request succeeded
- `response` (string): AI's text response
- `audio_response_base64` (string): AI's audio response as base64-encoded WAV
- `updated_medical_information` (object): Collected medical data
- `conversation_complete` (boolean): Whether all information is collected
- `error` (string, nullable): Error message if failed

---

## Python Examples

### Example 1: Send Text, Get Audio Response

```python
import requests
import base64

response = requests.post(
    "http://localhost:8000/api/v1/medical-chat",
    json={
        "message": "I have a fever and cough",
        "conversation_history": [],
        "medical_information": None,
        "prescription_data": None
    }
)

result = response.json()

# Get text response
print(f"Text: {result['response']}")

# Save audio response
if result['audio_response_base64']:
    audio_data = base64.b64decode(result['audio_response_base64'])
    with open('response.wav', 'wb') as f:
        f.write(audio_data)
    print("Audio saved to response.wav")
```

### Example 2: Send Audio, Get Audio Response

```python
import requests
import base64

# Load your audio file
with open('user_message.mp3', 'rb') as f:
    audio_data = f.read()

audio_base64 = base64.b64encode(audio_data).decode('utf-8')

# Send audio
response = requests.post(
    "http://localhost:8000/api/v1/medical-chat",
    json={
        "audio_base64": audio_base64,
        "conversation_history": [],
        "medical_information": None,
        "prescription_data": None
    }
)

result = response.json()

# The audio was transcribed and processed
print(f"Transcribed: {result['response']}")

# Save audio response
audio_response = base64.b64decode(result['audio_response_base64'])
with open('ai_response.wav', 'wb') as f:
    f.write(audio_response)
```

### Example 3: Complete Voice Conversation

```python
import requests
import base64

def chat_with_audio(audio_file_path, conversation_history, medical_info):
    """Send audio and get audio response."""
    
    # Load audio
    with open(audio_file_path, 'rb') as f:
        audio_data = f.read()
    
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    
    # Send request
    response = requests.post(
        "http://localhost:8000/api/v1/medical-chat",
        json={
            "audio_base64": audio_base64,
            "conversation_history": conversation_history,
            "medical_information": medical_info,
            "prescription_data": None
        }
    )
    
    return response.json()

# Start conversation
conversation = []
medical_info = None

# Turn 1
result1 = chat_with_audio("user_greeting.mp3", conversation, medical_info)
print(f"AI: {result1['response']}")

# Save AI's audio response
with open("ai_response_1.wav", "wb") as f:
    f.write(base64.b64decode(result1['audio_response_base64']))

# Update conversation
conversation.append({"role": "user", "content": result1['response']})
conversation.append({"role": "assistant", "content": result1['response']})
medical_info = result1['updated_medical_information']

# Continue conversation...
```

---

## JavaScript/Frontend Example

```javascript
// Send audio from browser
async function sendAudioMessage(audioBlob) {
  // Convert blob to base64
  const reader = new FileReader();
  reader.readAsDataURL(audioBlob);
  
  reader.onloadend = async () => {
    const base64Audio = reader.result.split(',')[1]; // Remove data:audio/...;base64,
    
    const response = await fetch('http://localhost:8000/api/v1/medical-chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        audio_base64: base64Audio,
        conversation_history: [],
        medical_information: null,
        prescription_data: null
      })
    });
    
    const result = await response.json();
    
    // Display text response
    console.log('AI:', result.response);
    
    // Play audio response
    if (result.audio_response_base64) {
      const audioData = atob(result.audio_response_base64);
      const audioBlob = new Blob([audioData], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);
      
      const audio = new Audio(audioUrl);
      audio.play();
    }
  };
}

// Record audio from microphone
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    const mediaRecorder = new MediaRecorder(stream);
    const audioChunks = [];
    
    mediaRecorder.ondataavailable = event => {
      audioChunks.push(event.data);
    };
    
    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
      sendAudioMessage(audioBlob);
    };
    
    // Start recording
    mediaRecorder.start();
    
    // Stop after 5 seconds
    setTimeout(() => mediaRecorder.stop(), 5000);
  });
```

---

## Audio Processing Details

### Input Audio
- **Formats Supported**: MP3, WAV, M4A, and other common formats
- **Encoding**: Base64
- **Processing**: Gemini transcribes the audio to text
- **Language**: Auto-detected (supports multiple languages)

### Output Audio
- **Format**: WAV
- **Encoding**: Base64
- **Voice**: "Kore" (Gemini's built-in voice)
- **Language**: Matches the conversation language
- **Quality**: High-quality speech synthesis

---

## Use Cases

### 1. Voice-Based Medical Intake
Perfect for:
- Elderly patients who prefer speaking
- Hands-free operation
- Accessibility features
- Multi-language support

### 2. Telemedicine Integration
- Record patient voice messages
- Get AI responses in audio format
- Maintain conversation context
- Collect structured medical data

### 3. Mobile Apps
- Voice-first mobile experience
- Background audio processing
- Offline recording, online processing
- Natural conversation flow

---

## Error Handling

### No Input Provided
```json
{
  "success": false,
  "response": null,
  "audio_response_base64": null,
  "error": "Either 'message' or 'audio_base64' must be provided"
}
```

### Audio Transcription Failed
```json
{
  "success": false,
  "response": null,
  "audio_response_base64": null,
  "error": "Failed to transcribe audio: [details]"
}
```

### Audio Generation Failed
- Text response will still be returned
- `audio_response_base64` will be `null`
- Error logged but request succeeds

---

## Performance Considerations

### Audio Processing Time
- **Transcription**: ~2-5 seconds for typical voice messages
- **Text Generation**: ~1-2 seconds
- **Audio Synthesis**: ~2-4 seconds
- **Total**: ~5-11 seconds for audio input → audio output

### Optimization Tips
1. **Compress audio** before encoding to base64
2. **Use shorter messages** for faster processing
3. **Cache conversation history** on client side
4. **Stream audio** if possible (future enhancement)

---

## Testing

### Run Audio Tests
```bash
python test_audio_chat.py
```

This will:
1. Test text input → audio output
2. Test audio input → audio output (if sample_audio.mp3 exists)
3. Run a complete conversation with audio responses
4. Save all audio responses as WAV files

### Manual Testing
1. Visit `http://localhost:8000/docs`
2. Try the `/medical-chat` endpoint
3. Paste base64-encoded audio in `audio_base64` field
4. Copy the `audio_response_base64` from response
5. Decode and save as WAV file to listen

---

## Limitations

1. **Audio file size**: Keep under 10MB for best performance
2. **Processing time**: Audio adds 5-10 seconds to response time
3. **Voice options**: Currently uses "Kore" voice only
4. **Format**: Output is always WAV format
5. **Rate limits**: Subject to Gemini API rate limits

---

## Future Enhancements

- [ ] Multiple voice options
- [ ] Streaming audio responses
- [ ] Real-time transcription
- [ ] Audio emotion detection
- [ ] Background noise filtering
- [ ] Custom voice training

---

## Support

For issues or questions:
- Check server logs for detailed error messages
- Ensure `GEMINI_API_KEY` is set correctly
- Verify audio file is properly encoded
- Test with the provided test script first
