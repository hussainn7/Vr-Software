import os
import sys
import time
import tkinter as tk
import threading
import signal
from dotenv import load_dotenv

# Load custom modules
from gui_adapter import GUI, GUI1, GUI2
from input_handler import InputHandler
from transcriber import VoiceProcessor

# Load environment variables
load_dotenv()

class TranslationApp:
    """
    Main controller for the voice translation application
    Acts as a state machine to manage scenes, recording, and translation
    """
    def __init__(self):
        # Initialize the root window
        self.root = tk.Tk()
        self.root.geometry("720x1080")
        self.root.configure(bg="#000000")
        self.root.title("Voice Translation App")
        
        # Make it fullscreen
        self.root.attributes("-fullscreen", True)
        
        # Set up keyboard bindings for exit
        self.root.bind("<Escape>", self.exit_app)
        self.root.bind("<Control-c>", self.exit_app)
        
        # Initialize state variables
        self.current_scene_index = 0
        self.is_recording = False
        self.is_processing = False
        self.is_showing_results = False
        self.last_transcription = ""
        self.last_translation = ""
        self.detected_language = ""
        
        # Initialize language settings - all use auto-detection now
        self.language_settings = [
            {"name": "Scene 1", "code": None, "target": "en"},  # GUI (Auto-detect to English)
            {"name": "Scene 2", "code": None, "target": "ru"},  # GUI1 (Auto-detect to Russian)
            {"name": "Scene 3", "code": None, "target": "en"}   # GUI2 (Auto-detect to English)
        ]
        
        # Initialize scenes using the adapter classes
        self.scenes = [
            GUI(self.root),      # Scene 1 (Speech to Text)
            GUI1(self.root),     # Scene 2 (Auto Detect)
            GUI2(self.root)      # Scene 3 (Video Record)
        ]
        
        # Pre-load all scenes to prevent flickering
        for scene in self.scenes:
            scene.setup()  # Initialize each scene
            scene.hide()   # But hide them initially
        
        # Initialize voice processor
        self.voice_processor = VoiceProcessor()
        
        # Initialize input handler for buttons
        self.input_handler = InputHandler()
        self.setup_button_handlers()
        
        # Start with the first scene (gui.py)
        self.load_current_scene()
        
    def setup_button_handlers(self):
        """Set up callbacks for button inputs"""
        self.input_handler.register_callback('button1', self.switch_scene)
        self.input_handler.register_callback('button2', self.trigger_transcription)
        self.input_handler.register_callback('button3', self.handle_context_action)
    
    def load_current_scene(self):
        """Load the current scene based on the scene index"""
        # Hide all scenes first
        for scene in self.scenes:
            scene.hide()
        
        # Set and show the current scene
        self.current_scene = self.scenes[self.current_scene_index]
        self.current_scene.show()
        
        # Update the window immediately to prevent flickering
        self.root.update_idletasks()
        
        # Reset state
        self.is_showing_results = False
        self.is_recording = False
        self.is_processing = False
    
    def switch_scene(self):
        """Switch to the next scene in the cycle"""
        if self.is_recording or self.is_processing:
            print("Cannot switch scene while recording or processing")
            return
            
        # Hide current scene first (smoother transition)
        self.current_scene.hide()
        
        # Move to the next scene
        self.current_scene_index = (self.current_scene_index + 1) % len(self.scenes)
        print(f"Switching to Scene {self.current_scene_index + 1} - {self.language_settings[self.current_scene_index]['name']}")
        
        # Show the new scene
        self.current_scene = self.scenes[self.current_scene_index]
        self.current_scene.show()
        
        # Update immediately
        self.root.update_idletasks()
        
        # Reset state
        self.is_showing_results = False
        self.is_recording = False
        self.is_processing = False
    
    def trigger_transcription(self):
        """Start the transcription process"""
        if self.is_recording or self.is_processing:
            print("Already recording or processing")
            return
            
        # Get the current language settings
        current_language = self.language_settings[self.current_scene_index]
        source_lang = current_language["code"]  # This will be None for auto-detection
        target_lang = current_language["target"]
        
        # Special behavior for Scene 3 - quick action mode
        auto_mode = (self.current_scene_index == 2)
        
        # Start the recording indicator
        self.is_recording = True
        self.show_recording_screen()
        
        # Process voice in a separate thread to avoid blocking the UI
        threading.Thread(
            target=self.process_voice_background,
            args=(source_lang, target_lang, auto_mode),
            daemon=True
        ).start()
    
    def process_voice_background(self, source_lang, target_lang, auto_mode):
        """Process voice recording and transcription in background"""
        try:
            # Set the processing flag
            self.is_processing = True
            
            # Process the voice input
            transcription, translation, detected_lang = self.voice_processor.process_voice(
                source_lang, target_lang, auto_mode
            )
            
            # Store the results
            self.last_transcription = transcription
            self.last_translation = translation
            self.detected_language = detected_lang
            
            # Show the results
            self.root.after(0, self.show_results)
            
        except Exception as e:
            print(f"Error processing voice: {e}")
            self.root.after(0, self.show_error, str(e))
        finally:
            # Reset the flags
            self.is_recording = False
            self.is_processing = False
    
    def show_recording_screen(self):
        """Show the recording screen"""
        if not self.current_scene:
            return
            
        self.current_scene.clear()
        self.current_scene.canvas.create_rectangle(0, 0, 720, 1080, fill="#000000", outline="")
        self.current_scene.center_text("Recording...", 500, font_size=50)
        self.root.update_idletasks()
    
    def show_results(self):
        """Show the transcription and translation results"""
        if not self.current_scene:
            return
            
        self.is_showing_results = True
        
        # Clear the canvas
        self.current_scene.clear()
        
        # Draw black background
        self.current_scene.canvas.create_rectangle(0, 0, 720, 1080, fill="#000000", outline="")
        
        # Use detected language for display
        display_language = self.detected_language.capitalize() if self.detected_language else "Auto-detected"
        
        # Show transcription header
        y_pos = 75
        self.current_scene.center_text(
            f"Transcription ({display_language})", 
            y_pos, font_size=30
        )
        y_pos += 40
        
        # Format and display the transcription
        self.format_and_display_text(self.last_transcription, y_pos)
        
        # If there's a translation, show it
        if self.last_translation:
            y_pos += 200  # Move down for translation
            
            # Get the actual target language - in cases where source language matches target,
            # the VoiceProcessor might have switched targets (like EN -> RU instead of EN -> EN)
            source_language = self.detected_language.lower() if self.detected_language else "unknown"
            target_language = "English" 
            
            # Set display name based on the source language (since target might have been switched)
            if source_language in ["english", "en"]:
                target_language = "Russian"
            elif source_language in ["russian", "ru"]:
                target_language = "English"
            else:
                # For other languages, use the configured target
                target_language = "English" if self.language_settings[self.current_scene_index]["target"] == "en" else "Russian"
                
            self.current_scene.center_text(
                f"Translation ({target_language})", 
                y_pos, font_size=30
            )
            y_pos += 40
            
            # Format and display the translation
            self.format_and_display_text(self.last_translation, y_pos)
        
        # Show instructions
        self.current_scene.center_text(
            "Press 3 to go back", 
            1000, font_size=30
        )
        
        # Update immediately
        self.root.update_idletasks()
    
    def format_and_display_text(self, text, start_y):
        """Format and display text with word wrapping"""
        if not text:
            return
            
        # Simple word wrapping
        lines = []
        current_line = ""
        max_chars = 40  # Adjust based on font size
        
        for word in text.split():
            if len(current_line + " " + word) <= max_chars:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
                
        if current_line:
            lines.append(current_line)
            
        # Display lines centered
        y_pos = start_y
        for line in lines:
            self.current_scene.center_text(line, y_pos, font_size=24)
            y_pos += 40  # Increased from 30 to 40 for better spacing
    
    def show_error(self, error_msg):
        """Show an error message"""
        if not self.current_scene:
            return
            
        self.current_scene.clear()
        self.current_scene.canvas.create_rectangle(0, 0, 720, 1080, fill="#000000", outline="")
        self.current_scene.center_text("Error", 400, font_size=50, fill="#FF0000")
        self.current_scene.center_text(error_msg, 500, font_size=30)
        self.current_scene.center_text("Press 3 to go back", 700, font_size=30)
        self.is_showing_results = True
        self.root.update_idletasks()
    
    def handle_context_action(self):
        """Handle context-dependent actions for Button 3"""
        if self.is_recording or self.is_processing:
            print("Cannot perform action while recording or processing")
            return
            
        if self.is_showing_results:
            # If showing results, go back to the scene
            self.current_scene.clear()
            self.current_scene.setup()  # Reload the scene content
            
            # Reset state
            self.is_showing_results = False
            
            # Update immediately
            self.root.update_idletasks()
            return
            
        # Scene-specific actions when not showing results
        if self.current_scene_index == 0:  # Scene 1 (Speech to Text)
            # Manual translation if needed
            print("Scene 1 context action")
        elif self.current_scene_index == 1:  # Scene 2 (Auto Detect)
            # Manual translation if needed
            print("Scene 2 context action")
        elif self.current_scene_index == 2:  # Scene 3 (Video Record)
            # Auto mode already handles this in trigger_transcription
            print("Scene 3 context action")
    
    def exit_app(self, event=None):
        """Exit the application cleanly"""
        print("Exiting application...")
        
        # Clean up resources
        self.input_handler.cleanup()
        self.voice_processor.cleanup()
        
        # Close the window
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Run the application main loop"""
        # Set up signal handlers for clean exit
        signal.signal(signal.SIGINT, lambda sig, frame: self.exit_app())
        
        # Start the main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.exit_app()


if __name__ == "__main__":
    app = TranslationApp()
    app.run() 