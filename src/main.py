from tkinter import Tk
import sys
import os
from ui.app_ui import AppUI
from speech.recognizer import Recognizer
from translation.translator import Translator
from video.recorder import Recorder
from utils import openai_manager  # Import utility functions from openai_manager

# OpenAI API key
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

class SpeechTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Translator App")
        
        # Setup OpenAI with the API key
        openai_manager.setup_openai_api(OPENAI_API_KEY)
        
        # Initialize components
        self.recognizer = Recognizer(language="en")  # Default to English
        self.translator = Translator(openai_manager)  # Pass the module
        self.recorder = Recorder()  # Video recorder
        
        # Initialize the UI
        self.ui = AppUI(self.root, self.recognizer, self.translator, self.recorder)

    def run(self):
        self.ui.setup_ui()
        self.root.mainloop()

if __name__ == "__main__":
    root = Tk()
    app = SpeechTranslatorApp(root)
    app.run()