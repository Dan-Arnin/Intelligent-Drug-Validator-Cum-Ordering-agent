import os
import json
import logging
import re
import base64
import tempfile
import wave
import io
from typing import List, Dict, Any, Optional, Tuple
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

MEDICAL_CHAT_SYSTEM_PROMPT = """You are a professional, friendly, and patient medical intake voice agent.
Your job is to collect accurate prescription-related information from the caller.
Follow the conversation flow exactly as described below.
Speak naturally, slowly, and clearly.
After asking a question, pause and wait for the customer to answer before continuing.
Always reply in the same language the user speaks in. If the user switches languages, switch with them.

GOALS

Identify the illness or medical condition the customer is suffering from.

Collect a full list of all medicines they have been prescribed and confirm if the information is correct.

RULES FOR THE AGENT

Do not provide medical advice.

Do not diagnose or make suggestions.

Only collect information.

Acknowledge the user responses briefly but politely.

Keep responses short and conversational.

If the user asks unrelated questions, gently redirect them back to the required information.

Match the user's language exactly when speaking.

CONVERSATION FLOW
Step 1 — Opening

Greet the user briefly and explain your purpose, Ask the first required question::

"Hello, I'm here to help collect information about your medical prescription details. To begin, can you tell me what disease or illness you are currently suffering from and what are the symptoms?"

(If the user greets you in another language, rephrase this greeting in that language.)

Step 2 — Question 1

→ Then stop and wait for their full response.
Store the user's answer into medical_information.reported_disease.

Step 3 — Acknowledge and Move to Question 2

After they answer, respond with a short acknowledgment:

"Thank you for sharing that."

(Translate to match the user's language.)

Step 4 — Question 2

Ask the second required question:

"Now, please list all the medicines you have been prescribed. Once you name them, I'll confirm if everything is correct."

→ Then stop and wait for their response.
Record their medications into medical_information.medications_provided_by_user.

Step 5 — Confirmation

Repeat the list back to them and ask:

"Did I get all those medicines correct?"

→ Wait for confirmation and record it in medical_information.medication_confirmation.

Step 6 — Closing

End politely:

"Thank you, your information has been recorded. Have a great day and take care."

(Translate as needed depending on the user's last language.)

IMPORTANT INSTRUCTIONS FOR EXTRACTING INFORMATION:

When the user provides their disease/symptoms, extract it and respond with JSON in this format:
{"extracted_disease": "the disease/symptoms they mentioned"}

When the user provides medicine names, extract them as a list and respond with JSON in this format:
{"extracted_medicines": ["medicine1", "medicine2", "medicine3"]}

When the user confirms or denies the medicine list, respond with JSON in this format:
{"confirmation": true} or {"confirmation": false}

Always include these JSON extractions in your response along with your conversational reply.
"""


class MedicalChatService:
    """Service for handling medical intake conversations using Google Gemini."""
    
    def __init__(self, model_name: str = "gemini-3-flash-preview"):
        """
        Initialize the medical chat service.
        
        Args:
            model_name: Name of the Gemini model to use
        """
        self.model_name = model_name
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLEAPIKEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLEAPIKEY environment variable must be set")
        
        self.client = genai.Client(api_key=api_key)
        logger.info(f"MedicalChatService initialized with model: {model_name}")
    
    def _build_conversation_context(
        self, 
        conversation_history: List[Dict[str, str]], 
        medical_information: Optional[Dict[str, Any]],
        prescription_data: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build context string from conversation history and medical information.
        
        Args:
            conversation_history: List of previous messages
            medical_information: Collected medical information
            prescription_data: Prescription data from OCR if available
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add prescription data if available
        if prescription_data:
            context_parts.append("PRESCRIPTION DATA AVAILABLE:")
            if prescription_data.get("doctor_info"):
                context_parts.append(f"Doctor: {prescription_data['doctor_info']}")
            if prescription_data.get("patient_info"):
                context_parts.append(f"Patient: {prescription_data['patient_info']}")
            if prescription_data.get("medicines"):
                medicines = [m.get("medicine_name", "") for m in prescription_data["medicines"]]
                context_parts.append(f"Prescribed medicines: {', '.join(medicines)}")
            context_parts.append("")
        
        # Add medical information if available
        if medical_information:
            context_parts.append("COLLECTED INFORMATION:")
            if medical_information.get("reported_disease"):
                context_parts.append(f"Disease/Symptoms: {medical_information['reported_disease']}")
            if medical_information.get("medications_provided_by_user"):
                meds = medical_information["medications_provided_by_user"]
                context_parts.append(f"Medications: {', '.join(meds)}")
            if medical_information.get("medication_confirmation") is not None:
                confirmed = medical_information["medication_confirmation"]
                context_parts.append(f"Medications confirmed: {confirmed}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _transcribe_audio(self, audio_base64: str) -> str:
        """
        Transcribe audio to text using Gemini.
        
        Args:
            audio_base64: Base64 encoded audio data
            
        Returns:
            Transcribed text
        """
        try:
            # Decode base64 audio
            audio_data = base64.b64decode(audio_base64)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
            try:
                # Upload audio file to Gemini
                logger.info("Uploading audio file to Gemini for transcription")
                myfile = self.client.files.upload(file=temp_audio_path)
                
                # Transcribe using Gemini
                response = self.client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=["Transcribe this audio clip. Only return the transcribed text, nothing else.", myfile]
                )
                
                transcribed_text = response.text.strip()
                logger.info(f"Audio transcribed: {transcribed_text[:50]}...")
                
                return transcribed_text
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
        
        except Exception as e:
            logger.error(f"Audio transcription failed: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def _generate_audio_response(self, text: str) -> str:
        """
        Generate audio response from text using Gemini TTS.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Base64 encoded audio data
        """
        try:
            logger.info("Generating audio response using Gemini TTS")
            
            # Using the new TTS model which returns raw PCM
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name='Kore',
                            )
                        )
                    ),
                )
            )
            
            # Extract raw PCM audio data
            # Check safely for response structure
            if not response.candidates or not response.candidates[0].content.parts:
                raise Exception("No audio content in response")
                
            pcm_data = response.candidates[0].content.parts[0].inline_data.data
            
            # Create a WAV file in memory from the raw PCM data
            # Gemini TTS typically returns: Mono (1 channel), 24000 Hz, 16-bit (2 bytes)
            with io.BytesIO() as wav_buffer:
                with wave.open(wav_buffer, "wb") as wf:
                    wf.setnchannels(1)        # Mono
                    wf.setsampwidth(2)        # 16-bit
                    wf.setframerate(24000)    # 24kHz
                    wf.writeframes(pcm_data)
                
                # Get the WAV file bytes
                wav_data = wav_buffer.getvalue()
                
                # Encode to base64
                audio_base64 = base64.b64encode(wav_data).decode('utf-8')
            
            logger.info(f"Audio response generated successfully ({len(audio_base64)} chars)")
            return audio_base64
        
        except Exception as e:
            logger.error(f"Audio generation failed: {str(e)}")
            # We don't want to crash the whole chat if audio fails, 
            # so we log deeply but raise to let the caller handle it (which catches and logs warning)
            raise Exception(f"Failed to generate audio response: {str(e)}")
    
    def _extract_information_from_response(self, response_text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract structured information from AI response.
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Tuple of (clean_response, extracted_data)
        """
        extracted_data = {}
        clean_response = response_text
        
        # Remove markdown code blocks (```json ... ```)
        clean_response = re.sub(r'```json\s*', '', clean_response)
        clean_response = re.sub(r'```\s*', '', clean_response)
        
        # Try to find JSON patterns in the response
        json_pattern = r'\{[^}]+\}'
        matches = re.findall(json_pattern, clean_response)
        
        for match in matches:
            try:
                data = json.loads(match)
                extracted_data.update(data)
                # Remove JSON from the response text
                clean_response = clean_response.replace(match, "").strip()
            except json.JSONDecodeError:
                continue
        
        # Clean up extra whitespace and newlines
        clean_response = re.sub(r'\n\s*\n', '\n', clean_response)  # Remove multiple blank lines
        clean_response = clean_response.strip()
        
        return clean_response, extracted_data
    
    def chat(
        self,
        user_message: Optional[str] = None,
        audio_base64: Optional[str] = None,
        conversation_history: List[Dict[str, str]] = None,
        medical_information: Optional[Dict[str, Any]] = None,
        prescription_data: Optional[Dict[str, Any]] = None,
        return_audio: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            user_message: The user's message (text)
            audio_base64: The user's message (audio as base64)
            conversation_history: Previous conversation messages
            medical_information: Collected medical information
            prescription_data: Prescription data from OCR if available
            return_audio: Whether to generate audio response
            
        Returns:
            Dictionary with response, audio_response_base64, updated medical information, and completion status
        """
        try:
            # Handle audio input if provided
            if audio_base64 and not user_message:
                logger.info("Transcribing audio input")
                user_message = self._transcribe_audio(audio_base64)
            
            if not user_message:
                raise ValueError("Either message or audio_base64 must be provided")
            
            if conversation_history is None:
                conversation_history = []
            # Build context
            context = self._build_conversation_context(
                conversation_history, 
                medical_information, 
                prescription_data
            )
            
            # Build the full conversation for Gemini
            messages = []
            
            # Add context as system message if available
            if context:
                messages.append(f"CONTEXT:\n{context}\n\nCONVERSATION:")
            
            # Add conversation history
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                messages.append(f"{role.upper()}: {content}")
            
            # Add current user message
            messages.append(f"USER: {user_message}")
            
            full_prompt = "\n".join(messages)
            
            logger.info(f"Sending chat request to Gemini")
            
            # Generate response
            response = self.client.models.generate_content(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=MEDICAL_CHAT_SYSTEM_PROMPT,
                    temperature=0.7
                ),
                contents=[full_prompt]
            )
            
            response_text = response.text
            
            # Extract structured information from response
            clean_response, extracted_data = self._extract_information_from_response(response_text)
            
            # Update medical information based on extracted data
            updated_medical_info = medical_information.copy() if medical_information else {}
            
            if "extracted_disease" in extracted_data:
                updated_medical_info["reported_disease"] = extracted_data["extracted_disease"]
            
            if "extracted_medicines" in extracted_data:
                updated_medical_info["medications_provided_by_user"] = extracted_data["extracted_medicines"]
            
            if "confirmation" in extracted_data:
                updated_medical_info["medication_confirmation"] = extracted_data["confirmation"]
            
            # Check if conversation is complete
            conversation_complete = (
                updated_medical_info.get("reported_disease") is not None and
                updated_medical_info.get("medications_provided_by_user") is not None and
                updated_medical_info.get("medication_confirmation") is not None
            )
            
            logger.info(f"Chat response generated. Complete: {conversation_complete}")
            
            # Generate audio response if requested
            audio_response_base64 = None
            if return_audio:
                try:
                    response_for_audio = clean_response if clean_response else response_text
                    audio_response_base64 = self._generate_audio_response(response_for_audio)
                except Exception as e:
                    logger.warning(f"Failed to generate audio response: {str(e)}")
                    # Continue without audio response
            
            return {
                "response": clean_response if clean_response else response_text,
                "audio_response_base64": audio_response_base64,
                "updated_medical_information": updated_medical_info,
                "conversation_complete": conversation_complete
            }
            
        except Exception as e:
            logger.error(f"Chat processing failed: {str(e)}")
            raise Exception(f"Medical chat failed: {str(e)}")
