"""
Test script for audio-enabled medical chat endpoint.
This demonstrates how to send audio and receive audio responses.
"""
import requests
import json
import base64
import wave
import os

BASE_URL = "http://localhost:8000/api/v1"


def save_audio_from_base64(audio_base64: str, filename: str):
    """Save base64 encoded audio to a WAV file."""
    audio_data = base64.b64decode(audio_base64)
    
    with open(filename, 'wb') as f:
        f.write(audio_data)
    
    print(f"✅ Audio saved to: {filename}")


def load_audio_to_base64(filename: str) -> str:
    """Load audio file and convert to base64."""
    with open(filename, 'rb') as f:
        audio_data = f.read()
    
    return base64.b64encode(audio_data).decode('utf-8')


def test_text_chat():
    """Test text-based chat (receives both text and audio response)."""
    print("\n" + "="*70)
    print("TEST 1: Text Input → Text + Audio Output")
    print("="*70)
    
    payload = {
        "message": "Hello, I need help with my prescription",
        "conversation_history": [],
        "medical_information": None,
        "prescription_data": None
    }
    
    print(f"\n📤 Sending text message: '{payload['message']}'")
    
    response = requests.post(f"{BASE_URL}/medical-chat", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ Success!")
        print(f"\n🤖 Text Response: {result['response']}")
        
        if result.get('audio_response_base64'):
            print(f"\n🔊 Audio Response: Received ({len(result['audio_response_base64'])} chars base64)")
            save_audio_from_base64(result['audio_response_base64'], "response_1.wav")
        else:
            print(f"\n⚠️  No audio response received")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)


def test_audio_chat():
    """Test audio-based chat (if you have an audio file)."""
    print("\n" + "="*70)
    print("TEST 2: Audio Input → Text + Audio Output")
    print("="*70)
    
    # Check if we have a sample audio file
    sample_audio = "sample_audio.mp3"
    
    if not os.path.exists(sample_audio):
        print(f"\n⚠️  Skipping audio test - no '{sample_audio}' file found")
        print(f"   To test audio input, place an MP3 file named '{sample_audio}' in this directory")
        return
    
    print(f"\n📤 Loading audio file: {sample_audio}")
    audio_base64 = load_audio_to_base64(sample_audio)
    
    payload = {
        "audio_base64": audio_base64,
        "conversation_history": [],
        "medical_information": None,
        "prescription_data": None
    }
    
    print(f"📤 Sending audio ({len(audio_base64)} chars base64)")
    
    response = requests.post(f"{BASE_URL}/medical-chat", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ Success!")
        print(f"\n📝 Transcribed Text: {result['response']}")
        
        if result.get('audio_response_base64'):
            print(f"\n🔊 Audio Response: Received ({len(result['audio_response_base64'])} chars base64)")
            save_audio_from_base64(result['audio_response_base64'], "response_2.wav")
        else:
            print(f"\n⚠️  No audio response received")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)


def test_conversation_flow():
    """Test a complete conversation with audio responses."""
    print("\n" + "="*70)
    print("TEST 3: Complete Conversation Flow (Text → Audio Responses)")
    print("="*70)
    
    conversation_history = []
    medical_info = None
    
    messages = [
        "Hello",
        "I have been suffering from fever and body ache for 2 days",
        "The doctor prescribed Paracetamol and Ibuprofen",
        "Yes, that's correct"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n--- Turn {i} ---")
        print(f"👤 User: {message}")
        
        payload = {
            "message": message,
            "conversation_history": conversation_history,
            "medical_information": medical_info,
            "prescription_data": None
        }
        
        response = requests.post(f"{BASE_URL}/medical-chat", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"🤖 Assistant: {result['response']}")
            
            # Save audio response
            if result.get('audio_response_base64'):
                audio_filename = f"conversation_turn_{i}.wav"
                save_audio_from_base64(result['audio_response_base64'], audio_filename)
            
            # Update conversation history
            conversation_history.append({
                "role": "user",
                "content": message
            })
            conversation_history.append({
                "role": "assistant",
                "content": result['response']
            })
            
            # Update medical information
            if result.get('updated_medical_information'):
                medical_info = result['updated_medical_information']
            
            if result.get('conversation_complete'):
                print(f"\n✅ Conversation Complete!")
                break
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            break
    
    if medical_info:
        print(f"\n📋 Final Collected Information:")
        print(json.dumps(medical_info, indent=2))


def create_sample_audio_instructions():
    """Show instructions for creating sample audio."""
    print("\n" + "="*70)
    print("HOW TO TEST WITH AUDIO INPUT")
    print("="*70)
    print("""
To test audio input functionality:

1. Record an audio file (MP3 format) saying something like:
   "Hello, I have a fever and headache"

2. Save it as 'sample_audio.mp3' in this directory

3. Run this script again

Alternatively, you can use any audio recording app on your phone:
- Record your voice
- Export as MP3
- Transfer to this directory as 'sample_audio.mp3'

The endpoint will:
1. Transcribe your audio using Gemini
2. Process the conversation
3. Generate an audio response
4. Return both text and audio
    """)


if __name__ == "__main__":
    try:
        print("\n🎙️  AUDIO-ENABLED MEDICAL CHAT TEST SUITE")
        print("="*70)
        
        # Test 1: Text input
        test_text_chat()
        
        # Test 2: Audio input (if available)
        test_audio_chat()
        
        # Test 3: Complete conversation
        test_conversation_flow()
        
        # Show instructions
        create_sample_audio_instructions()
        
        print("\n" + "="*70)
        print("✅ All tests completed!")
        print("="*70)
        print("\n📁 Check the current directory for generated audio files:")
        print("   - response_1.wav")
        print("   - conversation_turn_*.wav")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("Make sure the server is running on http://localhost:8000")
        print("\nStart the server with: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
