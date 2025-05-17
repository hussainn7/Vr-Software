# Constants for supported languages and utility functions for language management

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'ru': 'Russian',
    'ja': 'Japanese'
}

def get_language_name(code):
    """Return the language name for a given language code."""
    return SUPPORTED_LANGUAGES.get(code, "Unknown Language")

def get_language_code(name):
    """Return the language code for a given language name."""
    for code, lang in SUPPORTED_LANGUAGES.items():
        if lang.lower() == name.lower():
            return code
    return None

def list_supported_languages():
    """Return a list of supported languages."""
    return list(SUPPORTED_LANGUAGES.values())