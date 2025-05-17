import os
import tempfile
import speech_recognition as sr
from utils import openai_manager

class Recognizer:
    def __init__(self, language):
        self.language = language
        self.recognizer = sr.Recognizer()
        self.supported_languages = {
            'en': 'English',
            'ru': 'Russian',
            'ja': 'Japanese'
        }
        self.microphone = None
    
    def recognize_speech(self, audio_data=None):
        """
        Recognize speech from microphone or audio data
        If audio_data is None, it listens from microphone
        """
        if audio_data is None:
            # Record audio from microphone
            with sr.Microphone() as source:
                print(f"Listening in {self.supported_languages.get(self.language, 'Unknown language')}...")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5)
                
                # Save audio to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    temp_file.write(audio.get_wav_data())
                    temp_path = temp_file.name
            
            # Use OpenAI's Whisper API through our manager
            with open(temp_path, 'rb') as audio_file:
                result = openai_manager.speech_to_text(audio_file, self.language)
                
            # Clean up temporary file
            os.remove(temp_path)
            return result
        else:
            # Process provided audio data
            return openai_manager.speech_to_text(audio_data, self.language)
            
    def set_language(self, language):
        """Change the speech recognition language"""
        if language in self.supported_languages:
            self.language = language
            print(f"Speech recognition language set to {self.supported_languages[language]}")
        else:
            raise ValueError(f"Language {language} not supported")

    def get_supported_languages(self):
        """Return dict of supported language codes and names"""
        return self.supported_languages
        
    def is_language_supported(self, language):
        """Check if a language is supported"""
        return language in self.supported_languages