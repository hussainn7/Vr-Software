import threading
import time
import platform

# Try to import GPIO libraries, with fallback for non-Raspberry Pi environments
try:
    from gpiozero import Button
    GPIO_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    GPIO_AVAILABLE = False
    print("GPIO not available. Running in keyboard-only mode.")

# Check if we're on macOS
IS_MACOS = platform.system() == 'Darwin'

# For non-macOS, try to use the keyboard module
if not IS_MACOS:
    try:
        import keyboard
        KEYBOARD_AVAILABLE = True
    except (ImportError, ModuleNotFoundError):
        KEYBOARD_AVAILABLE = False
        print("Keyboard module not available.")
else:
    # On macOS, we'll use Tkinter bindings instead
    KEYBOARD_AVAILABLE = False
    print("On macOS, using Tkinter for keyboard input instead of keyboard module.")

class InputHandler:
    """
    Handles button inputs from GPIO pins and keyboard
    
    Button 1: Scene switch (GPIO 17, Key 1)
    Button 2: Transcription trigger (GPIO 27, Key 2)
    Button 3: Confirm/Translate/Back (GPIO 22, Key 3)
    """
    def __init__(self):
        self.callbacks = {
            'button1': [],
            'button2': [],
            'button3': []
        }
        
        self.running = False
        self.keyboard_thread = None
        self.buttons = {}
        self.root = None
        
        # Set up GPIO buttons if available
        if GPIO_AVAILABLE:
            self._setup_gpio()
            
        # Set up keyboard inputs if not on macOS
        if KEYBOARD_AVAILABLE and not IS_MACOS:
            self._setup_keyboard()
    
    def _setup_gpio(self):
        """Set up GPIO buttons"""
        try:
            # Define GPIO pin numbers
            pins = {
                'button1': 17,  # GPIO 17 for Button 1
                'button2': 27,  # GPIO 27 for Button 2
                'button3': 22   # GPIO 22 for Button 3
            }
            
            # Create button objects and set up callbacks
            for name, pin in pins.items():
                self.buttons[name] = Button(pin, pull_up=True)
                self.buttons[name].when_pressed = lambda btn=name: self._button_callback(btn)
                
            print("GPIO buttons initialized")
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
    
    def _setup_keyboard(self):
        """Set up keyboard input handling"""
        if not KEYBOARD_AVAILABLE:
            return
            
        # Map keys to button names
        self.key_mapping = {
            '1': 'button1',
            '2': 'button2',
            '3': 'button3'
        }
        
        # Start keyboard monitoring thread
        self.running = True
        self.keyboard_thread = threading.Thread(target=self._keyboard_monitor)
        self.keyboard_thread.daemon = True
        self.keyboard_thread.start()
        
        print("Keyboard input initialized")
        
    def setup_tkinter_bindings(self, root):
        """Set up Tkinter key bindings for macOS"""
        if not IS_MACOS:
            return
            
        self.root = root
        
        # Set up key bindings
        self.root.bind("1", lambda event: self._button_callback('button1'))
        self.root.bind("2", lambda event: self._button_callback('button2'))
        self.root.bind("3", lambda event: self._button_callback('button3'))
        
        print("Tkinter keyboard bindings initialized")
    
    def _keyboard_monitor(self):
        """Monitor keyboard inputs in a separate thread"""
        if not KEYBOARD_AVAILABLE:
            return
            
        while self.running:
            try:
                for key, button in self.key_mapping.items():
                    if keyboard.is_pressed(key):
                        self._button_callback(button)
                        # Sleep to avoid multiple triggers from a single press
                        time.sleep(0.3)
                
                # Short sleep to reduce CPU usage
                time.sleep(0.05)
            except Exception as e:
                print(f"Error in keyboard monitor: {e}")
                time.sleep(0.5)
    
    def _button_callback(self, button_name):
        """Handle button press events"""
        print(f"Button pressed: {button_name}")
        
        # Call all registered callbacks for this button
        for callback in self.callbacks.get(button_name, []):
            try:
                callback()
            except Exception as e:
                print(f"Error in button callback: {e}")
    
    def register_callback(self, button_name, callback):
        """
        Register a callback function for a button
        
        button_name: 'button1', 'button2', or 'button3'
        callback: function to call when the button is pressed
        """
        if button_name not in self.callbacks:
            self.callbacks[button_name] = []
            
        self.callbacks[button_name].append(callback)
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        # Stop keyboard thread
        if self.keyboard_thread and self.keyboard_thread.is_alive():
            self.keyboard_thread.join(timeout=1.0)
            
        # Clean up GPIO resources
        for button in self.buttons.values():
            try:
                button.close()
            except:
                pass
                
        # Clean up Tkinter bindings
        if IS_MACOS and self.root:
            try:
                self.root.unbind("1")
                self.root.unbind("2")
                self.root.unbind("3")
            except:
                pass

# Simple test function
def main():
    def button1_callback():
        print("Button 1 action: Switch scene")
        
    def button2_callback():
        print("Button 2 action: Start transcription")
        
    def button3_callback():
        print("Button 3 action: Confirm/Translate/Back")
    
    input_handler = InputHandler()
    input_handler.register_callback('button1', button1_callback)
    input_handler.register_callback('button2', button2_callback)
    input_handler.register_callback('button3', button3_callback)
    
    print("Input handler test started. Press 1, 2, or 3 keys (or GPIO buttons if available).")
    print("Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        input_handler.cleanup()

if __name__ == "__main__":
    main() 