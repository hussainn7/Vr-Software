import os
import time
import tempfile
import threading
import wave
import pyaudio
import openai
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AudioRecorder:
    """
    Records audio from the microphone
    """
    def __init__(self, rate=16000, channels=1, chunk=1024, format=pyaudio.paInt16):
        self.rate = rate
        self.channels = channels
        self.chunk = chunk
        self.format = format
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None
    
    def start_recording(self):
        """Start recording audio"""
        if self.is_recording:
            return
            
        self.frames = []
        self.is_recording = True
        
        # Start a new thread for recording
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
    def _record(self):
        """Record audio in a separate thread"""
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk)
                self.frames.append(data)
            except Exception as e:
                print(f"Error recording audio: {e}")
                break
    
    def stop_recording(self):
        """Stop recording audio"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
            
        return self.frames
    
    def save_recording(self, filename="recording.wav"):
        """Save the recorded audio to a file"""
        if not self.frames:
            return None
            
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            
        return filename
    
    def cleanup(self):
        """Clean up resources"""
        if self.stream:
            self.stream.close()
        self.audio.terminate()


class WhisperTranscriber:
    """
    Transcribes audio using OpenAI's Whisper API
    """
    def __init__(self, api_key=None):
        # Use the API key from environment variables or the provided one
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide it during initialization.")
        
        openai.api_key = self.api_key
    
    def transcribe(self, audio_file, language=None):
        """
        Transcribe audio file using Whisper API
        language: optional language code (e.g., 'en', 'ru', 'ja')
        
        Returns tuple of (transcription, detected_language)
        """
        try:
            with open(audio_file, "rb") as file:
                # Set up options - omit language for auto-detection
                options = {
                    "file": file, 
                    "model": "whisper-1",
                    "response_format": "verbose_json"  # Get detailed response with language
                }
                
                # Only specify language if explicitly provided and not None
                if language:
                    options["language"] = language
                
                # Call the API
                response = openai.Audio.transcribe(**options)
                
                # Extract the text and detected language
                if isinstance(response, str):
                    # Try to parse response if it's a string
                    try:
                        response_data = json.loads(response)
                        transcription = response_data.get("text", "")
                        detected_lang = response_data.get("language", None)
                    except:
                        transcription = response
                        detected_lang = None
                else:
                    # Access as object attributes or dictionary keys
                    transcription = getattr(response, "text", 
                                        response.get("text") if hasattr(response, "get") else "")
                    detected_lang = getattr(response, "language", 
                                         response.get("language") if hasattr(response, "get") else None)
                
                print(f"API detected language: {detected_lang}")
                return transcription, detected_lang
                
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return f"Transcription error: {e}", None


class Translator:
    """
    Translates text using OpenAI's GPT API
    """
    def __init__(self, api_key=None):
        # Use the API key from environment variables or the provided one
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide it during initialization.")
        
        openai.api_key = self.api_key
    
    def translate(self, text, source_lang, target_lang):
        """
        Translate text from source language to target language
        """
        if not text:
            return ""
            
        try:
            prompt = f"Translate the following {source_lang} text to {target_lang}:\n\n{text}"
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a translator. Provide only the translation without explanations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error translating text: {e}")
            return f"Translation error: {e}"
            
            
class VoiceProcessor:
    """
    Handles the full voice processing workflow
    """
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = WhisperTranscriber()
        self.translator = Translator()
        
    def process_voice(self, source_lang, target_lang=None, auto_mode=False):
        """
        Process voice recording, transcription, and translation
        
        source_lang: Language of the spoken input (e.g., 'en', 'ru', 'ja'), or None for auto-detection
        target_lang: Target language for translation (if None, determined by rules)
        auto_mode: If True, automatically translate without confirmation
        
        Returns a tuple of (transcription, translation, detected_language)
        """
        # Start recording
        print(f"Recording started (language: {source_lang or 'auto-detect'})...")
        self.recorder.start_recording()
        
        # Record for 5 seconds
        time.sleep(5)
        
        # Stop recording
        print("Recording stopped")
        self.recorder.stop_recording()
        
        # Save the recording to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        audio_file = self.recorder.save_recording(temp_file.name)
        
        # Transcribe the audio
        print(f"Transcribing in {source_lang or 'auto-detect mode'}...")
        transcription, detected_lang = self.transcriber.transcribe(audio_file, source_lang)
        print(f"Transcription: {transcription}")
        print(f"Detected language: {detected_lang}")
        
        # Convert detected language to standard code format if needed
        # Whisper might return full language name or code
        language_code_map = {
            "english": "en",
            "russian": "ru",
            "japanese": "ja",
            "french": "fr",
            "german": "de",
            "spanish": "es",
            "italian": "it",
            "chinese": "zh",
            "korean": "ko"
        }
        
        # Standardize detected language to code format (en, ru, ja, etc.)
        if detected_lang and detected_lang.lower() in language_code_map:
            detected_lang_code = language_code_map[detected_lang.lower()]
        else:
            detected_lang_code = detected_lang.lower() if detected_lang else None
        
        # Determine the source language either from input or detection
        actual_source_lang = source_lang or detected_lang_code or "en"
        
        # Determine target language if not specified
        if target_lang is None:
            # Default rules
            if actual_source_lang != "en":
                target_lang = "en"
            else:
                target_lang = "ru"
        else:
            # Force English->Russian and Russian->English regardless of scene
            if (actual_source_lang == "en" or detected_lang_code == "en" or 
                detected_lang and "english" in detected_lang.lower()):
                print("English speech detected, forcing translation to Russian")
                target_lang = "ru"
            elif (actual_source_lang == "ru" or detected_lang_code == "ru" or 
                  detected_lang and "russian" in detected_lang.lower()):
                print("Russian speech detected, forcing translation to English")
                target_lang = "en"
        
        # Translate if needed or in auto mode
        translation = None
        if auto_mode or target_lang != actual_source_lang:
            print(f"Translating from {actual_source_lang} to {target_lang}...")
            translation = self.translator.translate(transcription, actual_source_lang, target_lang)
            print(f"Translation: {translation}")
        
        # Clean up temporary file
        try:
            os.unlink(temp_file.name)
        except:
            pass
            
        # Convert language code to a more friendly name for display
        language_names = {
            "en": "english",
            "ru": "russian",
            "ja": "japanese",
            "fr": "french",
            "de": "german",
            "es": "spanish",
            "it": "italian",
            "zh": "chinese",
            "ko": "korean"
        }
        
        friendly_lang = language_names.get(detected_lang_code, detected_lang) if detected_lang else "unknown"
            
        return (transcription, translation, friendly_lang)
        
    def cleanup(self):
        """Clean up resources"""
        self.recorder.cleanup() 