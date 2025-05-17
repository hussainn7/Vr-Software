import os
import openai
from openai import OpenAI

# Global client
client = None

def setup_openai_api(api_key):
    """Set up the OpenAI API with the given key"""
    global client
    openai.api_key = api_key
    client = OpenAI(api_key=api_key)
    
    # Monitor usage to keep costs low
    print("OpenAI API initialized with cost optimization enabled")

def call_openai_api(prompt, model="gpt-3.5-turbo"):
    """Make a basic API call to OpenAI"""
    global client
    if not client:
        raise ValueError("OpenAI API not initialized. Call setup_openai_api first.")
        
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100  # Limit tokens to reduce costs
    )
    return response.choices[0].message.content

def translate_text(text, source_lang, target_lang):
    """Translate text from source language to target language"""
    if not text:
        return ""
        
    # Optimize prompt to reduce token usage
    prompt = f"Translate from {source_lang} to {target_lang}, text: {text}"
    return call_openai_api(prompt, model="gpt-3.5-turbo")

def speech_to_text(audio_data, language):
    """Convert speech audio to text in the specified language"""
    global client
    if not client:
        raise ValueError("OpenAI API not initialized. Call setup_openai_api first.")
    
    try:
        # Use Whisper model for audio transcription
        response = client.audio.transcriptions.create(
            file=audio_data,
            model="whisper-1",
            language=language
        )
        return response.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""

def manage_api_usage():
    return {
        "model": "gpt-3.5-turbo",  # Lower cost than GPT-4
        "max_tokens": 100,
        "optimization": "enabled"
    }