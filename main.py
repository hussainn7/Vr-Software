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
        self.is_scene_active = False  # New flag to track if scene is active
        self.live_transcription_active = False  # New flag for live transcription
        self.last_transcription = ""
        self.last_translation = ""
        self.detected_language = ""
        
        # Add cooldown system to prevent accidental re-entry
        self.last_action_time = 0
        self.cooldown_period = 1.0  # 1 second cooldown between state transitions
        
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
        
        # Set up Tkinter keyboard bindings if on macOS
        self.input_handler.setup_tkinter_bindings(self.root)
        
        # Start with the first scene (gui.py)
        self.load_current_scene()
        
    def setup_button_handlers(self):
        """Set up callbacks for button inputs"""
        self.input_handler.register_callback('button1', self.switch_scene)
        self.input_handler.register_callback('button3', self.handle_scene_action)
    
    def load_current_scene(self):
        """Load the current scene based on the scene index"""
        # Hide all scenes first
        for scene in self.scenes:
            scene.hide()
        
        # Reset state BEFORE showing the new scene
        self.is_showing_results = False
        self.is_recording = False
        self.is_processing = False
        self.is_scene_active = False
        self.live_transcription_active = False
        
        # Set and show the current scene
        self.current_scene = self.scenes[self.current_scene_index]
        self.current_scene.show()
        
        # Update the window immediately to prevent flickering
        self.root.update_idletasks()
    
    def switch_scene(self):
        """Switch to the next scene in the cycle - ONLY for scrolling between scenes"""
        # Apply cooldown to prevent accidental triggers
        current_time = time.time()
        if current_time - self.last_action_time < self.cooldown_period:
            print(f"Ignoring button press - cooldown active ({self.cooldown_period}s)")
            return
            
        # Button 1 should ONLY be used for scrolling between scenes
        # If we're in an active feature, DO NOT exit it - just ignore the button press
        if self.is_scene_active:
            print(f"Ignoring scene switch while in active feature. Use Button 3 to exit first.")
            return
        
        # First, stop any active processes in the current scene
        self.reset_state()
        # Hide current scene first (smoother transition)
        self.current_scene.hide()
        # Move to the next scene
        self.current_scene_index = (self.current_scene_index + 1) % len(self.scenes)
        print(f"Switching to Scene {self.current_scene_index + 1} - {self.language_settings[self.current_scene_index]['name']}")
        # Reset state BEFORE showing the new scene
        self.is_showing_results = False
        self.is_recording = False
        self.is_processing = False
        self.is_scene_active = False
        self.live_transcription_active = False
        # Show the new scene
        self.current_scene = self.scenes[self.current_scene_index]
        self.current_scene.show()
        # Update immediately
        self.root.update_idletasks()
        
        # Update last action time
        self.last_action_time = current_time
        
    def reset_state(self):
        """Reset all state flags and stop all processes"""
        self.stop_current_processes()
        self.is_scene_active = False
        self.live_transcription_active = False
        self.is_recording = False
        self.is_processing = False
        self.is_showing_results = False

    def handle_scene_action(self):
        """Handle scene-specific actions based on Button3 press"""
        # Apply cooldown to prevent accidental triggers
        current_time = time.time()
        if current_time - self.last_action_time < self.cooldown_period:
            print(f"Ignoring button press - cooldown active ({self.cooldown_period}s)")
            return
            
        # Update last action time immediately to prevent double-triggers
        self.last_action_time = current_time
        
        # FORCE EXIT ANY ACTIVE SCENE IMMEDIATELY when Button 3 is pressed
        if self.is_scene_active or self.is_showing_results:
            print(f"FORCE EXITING Scene {self.current_scene_index + 1} - Restoring initial state")
            # Kill any active processes immediately
            if hasattr(self, 'voice_processor') and self.voice_processor:
                try:
                    self.voice_processor.stop_live_transcription()
                except Exception as e:
                    print(f"Error stopping voice processor: {e}")
            
            # Force reset all state flags
            self.is_scene_active = False
            self.live_transcription_active = False
            self.is_recording = False
            self.is_processing = False
            self.is_showing_results = False
            
            # Kill any running threads or processes
            self.stop_current_processes()
            
            # COMPLETELY RELOAD THE SCENE FROM SCRATCH
            # This ensures we go back to the proper initial state
            print(f"Reloading scene {self.current_scene_index + 1} from scratch")
            
            # First hide the current scene
            self.current_scene.hide()
            
            # Completely recreate the scene object to ensure a fresh state
            scene_index = self.current_scene_index
            scene_classes = [GUI, GUI1, GUI2]
            self.scenes[scene_index] = scene_classes[scene_index](self.root)
            self.current_scene = self.scenes[scene_index]
            
            # Set up and show the fresh scene
            self.current_scene.setup()
            self.current_scene.show()
            
            # Force update the UI
            self.root.update_idletasks()
            
            # Set a longer cooldown after exiting to prevent accidental re-entry
            self.last_action_time = current_time
            return
            
        # If we're not in an active scene, activate the current scene
        print(f"Activating Scene {self.current_scene_index + 1}")
        self.is_scene_active = True
        
        # Scene-specific actions
        if self.current_scene_index == 0:  # Scene 1 (Transcription)
            self.start_live_transcription()
                
        elif self.current_scene_index == 1:  # Scene 2 (Translation)
            self.start_live_transcription()
                
        elif self.current_scene_index == 2:  # Scene 3 (Camera)
            try:
                # Start camera (placeholder for actual camera implementation)
                print("Camera started")
                self.camera_active = True
                
                # Show camera started message
                self.current_scene.clear() 
                
                # Get screen dimensions
                screen_width = self.root.winfo_width() or 720
                screen_height = self.root.winfo_height() or 1080
                center_x = screen_width / 2
                center_y = screen_height / 2
                
                # Create a black background to ensure visibility
                self.current_scene.canvas.create_rectangle(
                    0, 0, screen_width, screen_height, 
                    fill="#000000", outline=""
                )
                
                # Calculate the image position (assuming it's at the top 40% of the screen)
                image_center_y = screen_height * 0.3  # Image is at about 30% from the top
                
                # Position text BELOW the image
                title_y = int(screen_height * 0.55)  # Title at 55% from top (below image)
                status_y = int(screen_height * 0.7)  # Status at 70% from top
                dot_y = int(screen_height * 0.85)  # Dot at 85% from top
                
                # Add a visual indicator box for the title text
                self.current_scene.canvas.create_rectangle(
                    screen_width * 0.1,  # 10% from left
                    title_y - (int(screen_height * 0.12) * 0.8),  # Above text
                    screen_width * 0.9,  # 90% from left
                    title_y + (int(screen_height * 0.12) * 0.8),  # Below text
                    fill="#333333",  # Dark gray background
                    outline="#FFFF00",  # Yellow outline
                    width=3  # Thick outline
                )
                
                # Add a title below the image with much larger text
                self.current_scene.center_text(
                    "CAMERA MODE", 
                    title_y, 
                    font_size=int(screen_height * 0.12),  # 12% of screen height (much larger)
                    fill="#FFFF00"  # Bright yellow for better visibility
                )
                
                # Add a visual indicator box for the status text
                self.current_scene.canvas.create_rectangle(
                    screen_width * 0.1,  # 10% from left
                    status_y - (int(screen_height * 0.15) * 0.8),  # Above text
                    screen_width * 0.9,  # 90% from left
                    status_y + (int(screen_height * 0.15) * 0.8),  # Below text
                    fill="#333333",  # Dark gray background
                    outline="#FF0000",  # Red outline
                    width=3  # Thick outline
                )
                
                # Add the recording status below the title with very large font and bright red color
                self.current_scene.center_text(
                    "RECORDING", 
                    status_y, 
                    font_size=int(screen_height * 0.15),  # 15% of screen height (very large)
                    fill="#FF0000"  # Bright red
                )
                
                # Add a recording indicator dot at the bottom
                dot_radius = int(min(screen_width, screen_height) * 0.03)  # 3% of smaller dimension
                dot_x = center_x  # Center horizontally
                
                self.current_scene.canvas.create_oval(
                    dot_x - dot_radius, dot_y - dot_radius,
                    dot_x + dot_radius, dot_y + dot_radius,
                    fill="#FF0000", outline=""
                )
                
                # Force immediate update
                self.root.update()
                
                # Placeholder for actual camera functionality
                # You'd typically initialize the camera here and start a video stream
                # For now, we're just showing a message
                
                self.root.update_idletasks()
            except Exception as e:
                print(f"Camera error: {e}")
                self.show_error(f"Camera error: {str(e)}")
                self.is_scene_active = False
    
    def start_live_transcription(self):
        """Start continuous live transcription"""
        if self.live_transcription_active:
            return
            
        # Get the current language settings
        current_language = self.language_settings[self.current_scene_index]
        source_lang = current_language["code"]  # This will be None for auto-detection
        target_lang = current_language["target"]
        
        # Prepare the UI for live transcription
        self.current_scene.clear()
        self.current_scene.canvas.create_rectangle(0, 0, 720, 1080, fill="#000000", outline="")
        
        # Add a header - store the ID to update it later
        header_title = " " if self.current_scene_index == 1 else " "
        self.header_text_id = self.current_scene.center_text(header_title, 100, font_size=40)
        self.detected_language_text_id = self.current_scene.center_text("Listening...", 160, font_size=30)
        
        # Create a separator line
        self.current_scene.canvas.create_line(
            100, 200, 620, 200, fill="#FFFFFF", width=2
        )
        
        # This will hold the transcription text
        self.live_transcription_text_id = None
        
        # Start live transcription
        self.live_transcription_active = True
        self.voice_processor.start_live_transcription(
            source_lang=source_lang,
            target_lang=target_lang,
            callback=self.update_live_transcription
        )
        
        # Update UI immediately
        self.root.update_idletasks()
    
    def update_live_transcription(self, transcription, translation, detected_lang):
        """Callback for updating the live transcription UI"""
        if not self.live_transcription_active:
            return
            
        try:
            # Update detected language text
            display_language = detected_lang.capitalize() if detected_lang else "Detecting..."
            self.current_scene.canvas.itemconfig(
                self.detected_language_text_id,
                text=f"Detected: {display_language}"
            )
            
            # Clear previous text
            if self.live_transcription_text_id:
                self.current_scene.canvas.delete(self.live_transcription_text_id)
            
            # Determine what text to display based on the scene
            if self.current_scene_index == 1:  # Scene 2 (Translation)
                # For translation scene, show only the translated text (Russian)
                # Need to translate if not already done
                if transcription and (translation is None or translation == ""):
                    print(f"Need to translate: '{transcription}'")
                    # Always attempt to translate to Russian regardless of detected language
                    try:
                        # Get target language (Russian)
                        target_lang = self.language_settings[self.current_scene_index]["target"]
                        source_lang = "en"  # Default to English if we can't detect
                        
                        # If we have a detected language, use it
                        if detected_lang:
                            if "english" in detected_lang.lower() or "en" == detected_lang.lower():
                                source_lang = "en"
                            elif "russian" in detected_lang.lower() or "ru" == detected_lang.lower():
                                source_lang = "ru"
                            elif "korean" in detected_lang.lower() or "ko" == detected_lang.lower():
                                source_lang = "ko"
                            # Add more language detections as needed
                        
                        print(f"Translating from {source_lang} to {target_lang}...")
                        translation = self.voice_processor.translator.translate(
                            transcription, source_lang, target_lang
                        )
                        print(f"Translated to Russian: {translation}")
                    except Exception as e:
                        print(f"Translation error: {e}")
                        translation = "Translation error"
                
                # Display the translation or waiting message
                display_text = translation or "Waiting for speech to translate..."
                display_title = "Russian Translation"
            else:
                # For other scenes, show the transcription
                display_text = transcription or "Listening..."
                display_title = "Transcription"
                
            # Update the header to indicate what's being shown
            self.current_scene.canvas.itemconfig(
                self.header_text_id,
                text=display_title
            )
            
            # Get screen dimensions for adaptive sizing
            screen_width = self.root.winfo_width() or 720
            screen_height = self.root.winfo_height() or 1080
            
            # Make sure we have a black background for better visibility
            self.current_scene.canvas.create_rectangle(
                0, 0, screen_width, screen_height,
                fill="#000000", outline=""
            )
            
            # Calculate the position of the image (it's at the center of the screen)
            image_center_x = screen_width / 2
            image_center_y = screen_height * 0.4  # Image is at about 40% from the top
            
            # Position text BELOW the image (at about 70% from the top)
            text_position_y = int(screen_height * 0.7)  # Position text below the image
            
            # Use much larger font size for better visibility
            adaptive_font_size = int(screen_height * 0.08)  # 8% of screen height (much larger)
            adaptive_width = int(screen_width * 0.9)  # 90% of screen width
            
            # Format text with one word per line for better readability on VR display
            # Split the text into words and join with newlines
            words = display_text.split()
            formatted_text = "\n".join(words)
            
            # Display text with much larger font and white color
            self.live_transcription_text_id = self.current_scene.center_text(
                text=formatted_text,
                y=text_position_y - 100,  # Position higher to accommodate multiple lines
                font_size=adaptive_font_size,
                fill="#FFFFFF",  # White text for better visibility
                width=None  # No width constraint since we're manually formatting
            )
            
            # Force a complete redraw
            self.root.update()
            
            # Print confirmation that text is being displayed
            print(f"Displaying text on screen: {display_text[:50]}...")
            
            # Force a complete redraw of the window
            try:
                self.root.update()
            except Exception as e:
                print(f"Error updating window: {e}")
            
            # Update the window
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"Error updating live transcription: {e}")
    
    def stop_current_processes(self):
        """Stop any active recording or processing"""
        # If live transcription is active, stop it
        if self.live_transcription_active:
            self.voice_processor.stop_live_transcription()
            self.live_transcription_active = False
            
        # If recording is in progress, stop it
        if self.is_recording:
            # If there's an active voice processor recording, stop it
            try:
                self.voice_processor.recorder.stop_recording()
            except:
                pass
            
        # If camera is active, stop it
        if hasattr(self, 'camera_active') and self.camera_active:
            print("Camera stopped")
            # Here you would actually stop the camera
            self.camera_active = False
            
        # Reset all states
        self.is_recording = False
        self.is_processing = False
        self.is_scene_active = False
        self.is_showing_results = False
        
        # Print a confirmation that everything is stopped
        print("All processes stopped, ready for scene navigation")
    
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
        self.current_scene.center_text("Error", 400, font_size=50, fill="#FFFFFF")
        self.current_scene.center_text(error_msg, 500, font_size=30)
        self.is_showing_results = True
        self.root.update_idletasks()
    
    def exit_app(self, event=None):
        """Exit the application cleanly"""
        print("Exiting application...")
        
        # Clean up resources
        self.stop_current_processes()
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