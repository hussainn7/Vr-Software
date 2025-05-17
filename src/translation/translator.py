class Translator:
    def __init__(self, openai_manager):
        self.openai_manager = openai_manager
        self.supported_languages = {'en': 'English', 'ru': 'Russian', 'ja': 'Japanese'}
        self.current_target_language = 'en'

    def translate(self, text, source_lang=None, target_lang=None):
        if not text:
            return ""
            
        # Auto-detect source language if not provided
        if not source_lang:
            source_lang = self.detect_language(text)
            
        # Use current target language if not specified
        if not target_lang:
            target_lang = self.current_target_language
            
        # Skip translation if source and target are the same
        if source_lang == target_lang:
            return text
            
        if target_lang not in self.supported_languages:
            raise ValueError(f"Target language {target_lang} not supported.")
        
        # Use the translate_text function from openai_manager
        translated_text = self.openai_manager.translate_text(
            text, 
            self.supported_languages[source_lang], 
            self.supported_languages[target_lang]
        )
        return translated_text

    def batch_translate(self, texts, target_language):
        translations = {}
        for text in texts:
            translations[text] = self.translate(text, None, target_language)
        return translations

    def detect_language(self, text):
        # Simple language detection logic
        if not text:
            return 'en'  # Default to English for empty text
            
        text = text.lower()
        # Check for Cyrillic characters (Russian)
        if any(ord('а') <= ord(c) <= ord('я') for c in text):
            return 'ru'
        # Check for Japanese characters
        elif any('\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in text):
            return 'ja'
        # Default to English
        else:
            return 'en'
            
    def set_target_language(self, language):
        if language in self.supported_languages:
            self.current_target_language = language
        else:
            raise ValueError(f"Language {language} not supported")