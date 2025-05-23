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
    def __init__(self, rate=44100, channels=1, chunk=1024, format=pyaudio.paInt16):
        self.rate = rate
        self.channels = channels
        self.chunk = chunk
        self.format = format
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None
        self.continuous_mode = False
        self.buffer_seconds = 3  # Buffer size in seconds for continuous mode
        self.frames_lock = threading.Lock()  # Add lock for thread-safe access to frames
        
        # Check available audio devices
        self._check_audio_devices()
    
    def _check_audio_devices(self):
        """Check available audio input devices and select the best one"""
        try:
            print("\nChecking audio devices:")
            info = self.audio.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            
            # Find input devices
            input_devices = []
            for i in range(num_devices):
                device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxInputChannels') > 0:
                    input_devices.append((i, device_info))
                    print(f"  Input Device {i}: {device_info.get('name')}")
            
            if not input_devices:
                print("WARNING: No input devices found!")
            else:
                print(f"Found {len(input_devices)} input devices")
                
            # Try to find the default input device
            try:
                default_input = self.audio.get_default_input_device_info()
                print(f"Default input device: {default_input.get('name')} (index {default_input.get('index')})")
                self.input_device_index = default_input.get('index')
            except Exception as e:
                print(f"Could not get default input device: {e}")
                # If we can't get the default, use the first available input device
                if input_devices:
                    self.input_device_index = input_devices[0][0]
                    print(f"Using first available input device: {input_devices[0][1].get('name')}")
                else:
                    self.input_device_index = None
                    print("WARNING: No input device selected!")
        except Exception as e:
            print(f"Error checking audio devices: {e}")
            self.input_device_index = None
    
    def start_recording(self, continuous=False):
        """Start recording audio"""
        if self.is_recording:
            return
            
        self.frames = []
        self.is_recording = True
        self.continuous_mode = continuous
        
        print(f"Starting audio recording (continuous={continuous})")
        
        # Start a new thread for recording
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
    def _record(self):
        """Record audio in a separate thread"""
        try:
            # Open the audio stream with the selected input device if available
            kwargs = {
                'format': self.format,
                'channels': self.channels,
                'rate': self.rate,
                'input': True,
                'frames_per_buffer': self.chunk
            }
            
            # Add input device index if available
            if hasattr(self, 'input_device_index') and self.input_device_index is not None:
                kwargs['input_device_index'] = self.input_device_index
                
            self.stream = self.audio.open(**kwargs)
            print(f"Audio stream opened successfully with rate={self.rate}, channels={self.channels}")
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self.is_recording = False
            return
        
        # For continuous mode, maintain a rolling buffer
        if self.continuous_mode:
            max_frames = int(self.rate / self.chunk * self.buffer_seconds)
            frame_count = 0
            print_interval = int(self.rate / self.chunk)  # Print level info once per second
            
            while self.is_recording:
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    
                    # Check audio level periodically
                    frame_count += 1
                    if frame_count % print_interval == 0:
                        # Calculate audio level (simple RMS)
                        try:
                            import numpy as np
                            audio_array = np.frombuffer(data, dtype=np.int16)
                            rms = np.sqrt(np.mean(np.square(audio_array)))
                            print(f"Audio level: {rms:.2f}")
                        except ImportError:
                            pass
                    
                    with self.frames_lock:
                        self.frames.append(data)
                    
                    # Keep only the most recent frames
                    if len(self.frames) > max_frames:
                        with self.frames_lock:
                            self.frames = self.frames[-max_frames:]
                except Exception as e:
                    print(f"Error recording audio: {e}")
                    break
        else:
            # For regular mode, just record until stopped
            frame_count = 0
            print_interval = int(self.rate / self.chunk)  # Print level info once per second
            
            while self.is_recording:
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    
                    # Check audio level periodically
                    frame_count += 1
                    if frame_count % print_interval == 0:
                        # Calculate audio level (simple RMS)
                        try:
                            import numpy as np
                            audio_array = np.frombuffer(data, dtype=np.int16)
                            rms = np.sqrt(np.mean(np.square(audio_array)))
                            print(f"Audio level: {rms:.2f}")
                        except ImportError:
                            pass
                    
                    with self.frames_lock:
                        self.frames.append(data)
                except Exception as e:
                    print(f"Error recording audio: {e}")
                    break
        
        # Clean up
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def stop_recording(self):
        """Stop recording audio"""
        if not self.is_recording:
            print("Not currently recording")
            return self.frames
            
        print("Stopping audio recording")
        self.is_recording = False
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)
            print("Recording thread stopped")
        
        # Check if we have any frames
        if not self.frames:
            print("WARNING: No audio frames were recorded!")
        else:
            print(f"Recorded {len(self.frames)} audio frames")
            
        return self.frames
    
    def save_to_wav(self, filename=None):
        """Save recorded audio to a WAV file"""
        if not self.frames:
            print("No audio frames to save")
            return None
        
        print(f"Saving {len(self.frames)} audio frames")
        
        if filename is None:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                filename = temp_file.name
        
        # Save the audio data
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            audio_data = b''.join(self.frames)
            wf.writeframes(audio_data)
        
        # Check if the audio is mostly silence
        try:
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            rms = np.sqrt(np.mean(np.square(audio_array)))
            print(f"Overall audio level: {rms:.2f}")
            
            if rms < 50:  # Arbitrary threshold for silence
                print("WARNING: Audio appears to be mostly silence")
            
            # Normalize audio if levels are too low but not silent
            if 10 < rms < 500:
                print("Audio level is low, attempting to normalize...")
                try:
                    # Simple normalization to increase volume
                    max_possible = np.iinfo(np.int16).max
                    max_current = np.max(np.abs(audio_array))
                    if max_current > 0:  # Avoid division by zero
                        gain_factor = max_possible / max_current * 0.8  # 80% of max to avoid clipping
                        normalized = (audio_array * gain_factor).astype(np.int16)
                        
                        # Write normalized audio to a new file
                        normalized_filename = filename + ".normalized.wav"
                        with wave.open(normalized_filename, 'wb') as wf_norm:
                            wf_norm.setnchannels(self.channels)
                            wf_norm.setsampwidth(self.audio.get_sample_size(self.format))
                            wf_norm.setframerate(self.rate)
                            wf_norm.writeframes(normalized.tobytes())
                        
                        print(f"Normalized audio saved to {normalized_filename}")
                        return normalized_filename
                except Exception as e:
                    print(f"Error normalizing audio: {e}")
                    # Fall back to original file if normalization fails
        except ImportError:
            pass
        
        print(f"Audio saved to {filename}")
        return filename
    
    def cleanup(self):
        """Clean up resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        self.audio.terminate()


class WhisperTranscriber:
    """Transcribes audio using OpenAI's Whisper API"""
    def __init__(self, api_key=None):
        # Use the API key from environment variables or the provided one
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide it during initialization.")
        
        openai.api_key = self.api_key
        
        # Print a confirmation that the API key is set
        print(f"OpenAI API key configured: {self.api_key[:5]}...{self.api_key[-4:]}")
        
    def transcribe(self, audio_file, language=None, max_retries=2):
        """
        Transcribe audio file using Whisper API
        language: optional language code (e.g., 'en', 'ru', 'ja')
        max_retries: number of retries if transcription fails
        
        Returns tuple of (transcription, detected_language)
        """
        for attempt in range(max_retries + 1):
            try:
                print(f"Transcription attempt {attempt+1}/{max_retries+1}")
                print(f"Attempting to transcribe audio file: {audio_file}")
                # Check if file exists
                if not os.path.exists(audio_file):
                    print(f"Error: Audio file not found: {audio_file}")
                    return "", ""
                
                # Check file size
                file_size = os.path.getsize(audio_file)
                print(f"Audio file size: {file_size} bytes")
                
                if file_size == 0:
                    print("Error: Audio file is empty")
                    return "", ""
                elif file_size < 5000:  # Less than 5KB is suspiciously small
                    print("Warning: Audio file is very small, may not contain enough speech data")
                    
                # Open the audio file
                with open(audio_file, "rb") as file:
                    # Call the Whisper API using the updated client format
                    options = {}
                    if language:
                        options["language"] = language
                    else:
                        # If no language specified, try to detect English
                        options["language"] = "en"
                        print("No language specified, defaulting to English detection")
                    
                    # Add additional options for better recognition
                    options["temperature"] = 0.2  # Slightly higher temperature for more flexibility
                    
                    try:
                        # Try the new client format first
                        from openai import OpenAI
                        client = OpenAI(api_key=self.api_key)
                        
                        print("Using new OpenAI client format with options:", options)
                        response = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=file,
                            **options
                        )
                        
                        # Extract the transcription text
                        transcription = response.text
                        detected_language = "auto-detected"  # New API doesn't return language
                        
                    except (ImportError, AttributeError) as e:
                        print(f"Error with new client format: {e}, falling back to legacy format")
                        # Fall back to legacy format
                        response = openai.Audio.transcribe(
                            model="whisper-1",
                            file=file,
                            **options
                        )
                        
                        # Extract the transcription text
                        transcription = response.get("text", "")
                        detected_language = response.get("language", "")
                    
                    if transcription:
                        print(f"Transcription successful: '{transcription}'")
                        return transcription, detected_language
                    else:
                        print("Transcription returned empty result")
                        
                        # If this is not the last attempt, try with different settings
                        if attempt < max_retries:
                            print("Retrying with different settings...")
                            # Try with different temperature on retry
                            options["temperature"] = 0.4 + (attempt * 0.2)  # Increase temperature with each retry
                            continue
                            
                # If we've exhausted all retries or got a result, return what we have
                return transcription, detected_language
                
            except Exception as e:
                print(f"Transcription error: {e}")
                import traceback
                traceback.print_exc()
                
            return "", ""


class Translator:
    """Translates text using OpenAI's GPT API"""
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
        if not text or text.strip() == "":
            print("No text to translate")
            return ""
            
        try:
            # Prepare the prompt for translation
            prompt = f"Translate the following {source_lang} text to {target_lang}:\n\n{text}\n\nTranslation:"
            
            print(f"Translating from {source_lang} to {target_lang}...")
            
            try:
                # Try the new client format first
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key)
                
                print("Using new OpenAI client format for translation")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional translator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1024
                )
                
                # Extract the translation
                translation = response.choices[0].message.content.strip()
                
            except (ImportError, AttributeError):
                # Fall back to legacy format
                print("Falling back to legacy OpenAI API format for translation")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional translator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1024
                )
                
                # Extract the translation
                translation = response.choices[0].message.content.strip()
            
            print(f"Translation successful: {translation[:50]}...")
            return translation
            
        except Exception as e:
            print(f"Translation error: {e}")
            import traceback
            traceback.print_exc()
            return ""


class VoiceProcessor:
    """Handles the full voice processing workflow"""
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = WhisperTranscriber()
        self.translator = Translator()
        self.live_mode = False
        self.processing_thread = None
        self.should_process = False
        self.callback = None
        
    def start_live_transcription(self, source_lang=None, target_lang=None, callback=None):
        """
        Start continuous live transcription
        
        source_lang: Language of the spoken input, or None for auto-detection
        target_lang: Target language for translation, or None for auto-detection
        callback: Function to call with new transcription results
        """
        if self.live_mode:
            return
            
        self.live_mode = True
        self.should_process = True
        self.callback = callback
        
        # Start recording in continuous mode
        self.recorder.start_recording(continuous=True)
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._live_processing_loop,
            args=(source_lang, target_lang)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        print(f"Live transcription started (language: {source_lang or 'auto-detect'})...")
        
    def _live_processing_loop(self, source_lang, target_lang):
        """Background thread for live processing"""
        last_process_time = 0
        last_transcription = ""  # Track last transcription to avoid duplicates
        process_interval = 0.3  # Process every 0.3 seconds for faster response
        
        while self.should_process:
            current_time = time.time()
            
            # Process at shorter intervals for more real-time feedback
            if current_time - last_process_time >= process_interval and self.recorder.frames:
                last_process_time = current_time
                
                # Make a copy of the current frames
                with self.recorder.frames_lock:
                    frames_copy = self.recorder.frames.copy()
                    # Clear frames to prevent reprocessing the same audio
                    self.recorder.frames.clear()
                
                try:
                    # Process only if we have enough audio data
                    if frames_copy and len(frames_copy) > 5:  # Ensure we have at least some audio data
                        # Join the audio frames
                        audio_data = b''.join(frames_copy)
                        
                        # Skip all the energy analysis and just process the audio directly
                        # This makes it more responsive and simpler
                        
                        # Create a temporary file for the audio
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                            audio_file = temp_file.name
                            
                        # Save the audio data
                        with wave.open(audio_file, 'wb') as wf:
                            wf.setnchannels(self.recorder.channels)
                            wf.setsampwidth(self.recorder.audio.get_sample_size(self.recorder.format))
                            wf.setframerate(self.recorder.rate)
                            wf.writeframes(audio_data)
                        
                        # Transcribe the audio
                        transcription, detected_lang = self.transcriber.transcribe(audio_file, source_lang)
                        
                        # Simple processing - just use the transcription directly
                        if not transcription.strip():
                            print("Empty transcription, skipping")
                            continue
                        
                        # Skip if it's exactly the same as the last transcription
                        if transcription.strip() == last_transcription.strip():
                            print(f"Duplicate transcription, skipping")
                            continue
                            
                        # Update last transcription
                        last_transcription = transcription.strip()
                        
                        if detected_lang:
                            print(f"API detected language: {detected_lang}")
                            
                        # Map language names to codes for consistency
                        language_code_map = {
                            "english": "en",
                            "russian": "ru",
                            "spanish": "es",
                            "french": "fr",
                            "german": "de",
                            "japanese": "ja",
                            "italian": "it",
                            "chinese": "zh",
                            "korean": "ko"
                        }
                        
                        # Standardize language code
                        if detected_lang and detected_lang.lower() in language_code_map:
                            detected_lang_code = language_code_map[detected_lang.lower()]
                        else:
                            detected_lang_code = detected_lang.lower() if detected_lang else None
                        
                        # Determine source and target languages
                        actual_source_lang = source_lang or detected_lang_code or "en"
                        
                        # Handle translation based on detected language
                        translation = None
                        
                        # If we have a target language and a transcription
                        if target_lang and transcription and detected_lang_code:
                            # Logic for Russian translation (target_lang = "ru")
                            if target_lang == "ru" and detected_lang_code == "en":
                                print(f"Translating English to Russian...")
                                translation = self.translator.translate(transcription, "en", "ru")
                            
                            # Logic for English translation (target_lang = "en")
                            elif target_lang == "en" and detected_lang_code == "ru":
                                print(f"Translating Russian to English...")
                                translation = self.translator.translate(transcription, "ru", "en")
                            
                            # Special case for other detected languages
                            elif detected_lang_code not in ["en", "ru"]:
                                # Always translate other languages to the target
                                print(f"Translating {detected_lang} to {target_lang}...")
                                translation = self.translator.translate(transcription, detected_lang_code, target_lang)
                        
                        # Clean up temp file
                        try:
                            os.unlink(audio_file)
                        except:
                            pass
                        
                        # Call the callback function with results
                        if self.callback:
                            print(f"Displaying text on screen: {transcription}")
                            self.callback(transcription, translation, detected_lang)
                            
                except Exception as e:
                    print(f"Live processing error: {e}")
                    
            # Sleep a bit to reduce CPU usage
            time.sleep(0.1)
        
    def stop_live_transcription(self):
        """Stop live transcription"""
        if not self.live_mode:
            return
            
        self.should_process = False
        self.live_mode = False
        
        # Stop recording
        self.recorder.stop_recording()
        
        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
            
        print("Live transcription stopped")
        
    def process_voice(self, source_lang, target_lang=None, auto_mode=False):
        """
        Process voice recording, transcription, and translation
        
        source_lang: Language of the spoken input (e.g., 'en', 'ru', 'ja'), or None for auto-detection
        target_lang: Target language for translation (if None, determined by rules)
        auto_mode: If True, automatically translate without confirmation
        
        Returns a tuple of (transcription, translation, detected_language)
        """
        print("Recording... Speak now.")
        
        # Start recording
        self.recorder.start_recording()
        
        # Record for 10 seconds (increased from 5 for better speech capture)
        print("Recording for 10 seconds...")
        time.sleep(10)
        
        # Stop recording
        print("Recording stopped. Processing...")
        self.recorder.stop_recording()
        
        # Save to temporary file
        audio_file = self.recorder.save_to_wav()
        
        if not audio_file:
            print("No audio recorded")
            return "", "", ""
            
        # Transcribe the audio
        transcription, detected_language = self.transcriber.transcribe(audio_file, source_lang)
        
        print(f"Detected language: {detected_language}")
        print(f"Transcription: {transcription}")
        
        # Determine target language based on detected language
        translation = None
        
        if transcription:
            # If target language is specified, use it
            if target_lang:
                translation = self.translator.translate(transcription, detected_language or source_lang or "en", target_lang)
            # Otherwise, determine based on detected language
            elif detected_language and "english" in detected_language.lower():
                translation = self.translator.translate(transcription, "en", "ru")
            elif detected_language and "russian" in detected_language.lower():
                translation = self.translator.translate(transcription, "ru", "en")
            
            if translation:
                print(f"Translation: {translation}")
        
        # Clean up the temporary file
        try:
            os.unlink(audio_file)
        except:
            pass
            
        return transcription, translation, detected_language
        
    def cleanup(self):
        """Clean up resources"""
        self.stop_live_transcription()
        self.recorder.cleanup()
