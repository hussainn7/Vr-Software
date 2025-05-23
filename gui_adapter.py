import os
import sys
import tkinter as tk
from tkinter import Canvas, PhotoImage
from PIL import Image, ImageTk
from pathlib import Path
import math

class GUIAdapter:
    """Base adapter class for GUI files"""
    def __init__(self, master=None):
        self.master = master
        self.canvas = None
        self.assets = {}
        self.is_visible = False
        self.mirrored = True  # Enable mirroring by default for VR glasses
        self.rotated = True  # Enable 90 degree rotation to the left
        
    def setup(self):
        """To be implemented by child classes"""
        pass
        
    def load(self):
        """Load the GUI content"""
        self.setup()
        self.is_visible = True
        return self.canvas
        
    def clear(self):
        """Clear the canvas"""
        if self.canvas:
            self.canvas.delete("all")
            
    def hide(self):
        """Hide the canvas"""
        if self.canvas and self.is_visible:
            self.canvas.place_forget()
            self.is_visible = False
            
    def show(self):
        """Show the canvas"""
        if self.canvas and not self.is_visible:
            self.canvas.place(x=0, y=0)
            self.is_visible = True
            
    def show_text(self, text, x, y, font_size=40, anchor="nw", fill="#FFFFFF", font_family="Inter ExtraBold"):
        """Show text on the canvas"""
        if self.canvas:
            return self.canvas.create_text(
                x, y,
                text=text,
                anchor=anchor,
                fill=fill,
                font=(font_family, font_size * -1)
            )
    
    def center_text(self, text, y, font_size=40, fill="#FFFFFF", font_family="Arial Bold", width=None):
        """Show centered text on the canvas with simple mirroring for VR glasses and rotation"""
        if self.canvas:
            # Get canvas dimensions for proper centering
            canvas_width = self.canvas.winfo_width() or 720  # Default to 720 if not yet rendered
            canvas_height = self.canvas.winfo_height() or 1080  # Default to 1080 if not yet rendered
            
            # Make font size larger for better visibility but not too large to cause cutoff
            scaled_font_size = int(font_size * 1.2)  # Reduced from 1.5 to prevent cutoff
            
            # Calculate y position as a percentage of screen height for better scaling
            # Adjust to ensure text is not cut off at the bottom
            y_percent = y / 1080  # Convert fixed y to percentage of reference height
            scaled_y = int(y_percent * canvas_height)  # Apply percentage to actual height
            
            # Create text with optional width constraint for wrapping
            # Use the provided fill color (default is white)
            kwargs = {
                "text": text,
                "anchor": "center",
                "fill": fill,  # Use the provided fill color
                "font": (font_family, scaled_font_size),
                "justify": "center"
            }
            
            # Add width parameter if provided (for text wrapping)
            # Use a much smaller width to prevent text from being cut off at edges
            if width:
                kwargs["width"] = width * 0.7  # Reduce width by 30% to prevent cutoff
            else:
                # Set a default width that's 60% of the canvas width to prevent cutoff
                kwargs["width"] = canvas_width * 0.6
            
            # If mirroring is enabled, reverse the text
            if self.mirrored:
                # Simple mirroring - just reverse the text
                mirrored_text = text[::-1]
                kwargs["text"] = mirrored_text
            
            # If rotation is enabled, swap x and y coordinates (90 degrees left rotation)
            if self.rotated:
                # For 90 degrees left rotation, adjust positioning to respect the y parameter
                # Use the provided y position for the rotated x coordinate
                rotated_x = scaled_y  # The original y becomes the x coordinate
                rotated_y = canvas_width / 2  # Center horizontally in rotated view
                
                # Create the main text - no outline/shadow to keep it clean
                text_id = self.canvas.create_text(
                    rotated_x,
                    rotated_y,
                    angle=90,  # Rotate text 90 degrees
                    **kwargs
                )
            else:
                # Standard non-rotated display - use center of canvas
                text_id = self.canvas.create_text(
                    canvas_width / 2,  # Center horizontally
                    scaled_y,          # Use calculated vertical position
                    **kwargs
                )
            
            return text_id
            
    def show_transcription(self, text):
        """Show transcription text on a black background"""
        self.clear()  # Clear all canvas items, including images
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width() or 720  # Default to 720 if not yet rendered
        canvas_height = self.canvas.winfo_height() or 1080  # Default to 1080 if not yet rendered
        
        # Create black background covering the entire canvas
        # Make sure there are no other elements like gray bars
        self.canvas.create_rectangle(0, 0, canvas_width, canvas_height, fill="#000000", outline="")
        
        # If text is empty, just show a blank black screen
        if not text or text.strip() == "":
            return
            
        # Show the transcription text with word wrapping
        lines = []
        current_line = ""
        # Further reduce max_chars to prevent text from being cut off at edges
        max_chars = 20  # Significantly reduced to prevent text cutoff
        
        # Split text into words and handle word wrapping
        for word in text.split():
            # If adding this word would exceed max_chars, start a new line
            if len(current_line + " " + word) <= max_chars:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
                
        # Add the last line if it has content
        if current_line:
            lines.append(current_line)
        
        # If no lines were created (e.g., single very long word), split the text manually
        if not lines and text:
            # Split the text into chunks of max_chars
            for i in range(0, len(text), max_chars):
                lines.append(text[i:i+max_chars])
        
        # Calculate vertical centering with more space at top and bottom
        total_height = len(lines) * 60  # Increased spacing between lines
        
        # Start higher up on the screen to avoid bottom cutoff
        start_y = (canvas_height - total_height) / 2 - 50  # Shift up by 50 pixels
        
        # Ensure start_y is not too low or too high
        if start_y < 150:
            start_y = 150  # Increased minimum top margin
        if start_y + total_height > canvas_height - 150:
            start_y = canvas_height - total_height - 150  # Ensure bottom margin
            
        y_pos = start_y  # Start position adjusted vertically
        
        # Display each line with proper spacing
        for line in lines:
            # Use white text (#FFFFFF) instead of yellow
            self.center_text(line, y_pos, font_size=25, fill="#FFFFFF")  # Changed to white
            y_pos += 60  # Increased spacing between lines for better readability


class GUI(GUIAdapter):
    """Adapter for gui.py (Scene 1 - Live Transcription)"""
    def __init__(self, master=None):
        super().__init__(master)
        
    def setup(self):
        if self.master is None:
            self.master = tk.Tk()
        if self.canvas is None:
            # For 90 degree rotation, swap width and height
            if self.rotated:
                width = 1080
                height = 720
            else:
                width = 720
                height = 1080
                
            # Center the window on the screen
            self.master.update_idletasks()
            x = (self.master.winfo_screenwidth() // 2) - (width // 2)
            y = (self.master.winfo_screenheight() // 2) - (height // 2)
            self.master.geometry(f"{width}x{height}+{x}+{y}")
            
            # Create canvas with black background
            self.canvas = Canvas(
                self.master,
                width=width,
                height=height,
                bg="#000000",  # Pure black background
                highlightthickness=0,  # Remove any border
                borderwidth=0  # Remove any border
            )
            self.canvas.place(x=0, y=0)  # Position at top-left corner
            self.master.configure(bg="#000000")
            
            # Create the canvas with rotated dimensions
            self.canvas = Canvas(
                self.master,
                bg="#000000",
                height=height,
                width=width,
                bd=0,
                highlightthickness=0,
                relief="ridge"
            )
            
            # Set the assets path
            script_dir = Path(__file__).parent
            assets_path = script_dir / "assets" / "frame0"
            
            # Load image
            try:
                image_path = assets_path / "image_1.png"
                
                if self.rotated:
                    # Load with PIL to rotate
                    pil_image = Image.open(str(image_path))
                    pil_image = pil_image.rotate(90, expand=True)  # Rotate 90 degrees left
                    image = ImageTk.PhotoImage(pil_image)
                    self.assets["image_1.png"] = image
                    
                    # Place the rotated image
                    self.canvas.create_image(
                        width / 2,  # Centered horizontally in the rotated canvas
                        height / 2,  # Centered vertically in the rotated canvas
                        image=image,
                        anchor="center"
                    )
                else:
                    # Standard non-rotated display
                    image = PhotoImage(file=str(image_path))
                    self.assets["image_1.png"] = image
                    
                    # Place the image at the center of the canvas
                    self.canvas.create_image(
                        360.0,  # Centered horizontally
                        425.0,
                        image=image
                    )
            except Exception as e:
                print(f"Error loading image: {e}")
            
            # Add centered text with larger font
            self.center_text(" ", 711.0, font_size=70)
            
            self.master.resizable(False, False)
        
        # Ensure the canvas is displayed
        self.canvas.place(x=0, y=0)
        self.is_visible = True


class GUI1(GUIAdapter):
    """Adapter for gui1.py (Scene 2 - Russian Translation)"""
    def __init__(self, master=None):
        super().__init__(master)
        
    def setup(self):
        if self.master is None:
            self.master = tk.Tk()
        if self.canvas is None:
            # For 90 degree rotation, swap width and height
            if self.rotated:
                width = 1080
                height = 720
            else:
                width = 720
                height = 1080
                
            # Center the window on the screen
            self.master.update_idletasks()
            x = (self.master.winfo_screenwidth() // 2) - (width // 2)
            y = (self.master.winfo_screenheight() // 2) - (height // 2)
            self.master.geometry(f"{width}x{height}+{x}+{y}")
            self.master.configure(bg="#000000")
            
            # Create the canvas with rotated dimensions
            self.canvas = Canvas(
                self.master,
                bg="#000000",
                height=height,
                width=width,
                bd=0,
                highlightthickness=0,
                relief="ridge"
            )
            
            # Set the assets path
            script_dir = Path(__file__).parent
            assets_path = script_dir / "assets" / "frame1"
            
            # Load image
            try:
                image_path = assets_path / "image_1.png"
                
                if self.rotated:
                    # Load with PIL to rotate
                    pil_image = Image.open(str(image_path))
                    pil_image = pil_image.rotate(90, expand=True)  # Rotate 90 degrees left
                    image = ImageTk.PhotoImage(pil_image)
                    self.assets["image_1.png"] = image
                    
                    # Place the rotated image
                    self.canvas.create_image(
                        width / 2,  # Centered horizontally in the rotated canvas
                        height / 2,  # Centered vertically in the rotated canvas
                        image=image,
                        anchor="center"
                    )
                else:
                    # Standard non-rotated display
                    image = PhotoImage(file=str(image_path))
                    self.assets["image_1.png"] = image
                    
                    # Place the image at the center of the canvas
                    self.canvas.create_image(
                        360.0,  # Centered horizontally
                        401.0,
                        image=image
                    )
            except Exception as e:
                print(f"Error loading image: {e}")
            
            # Add centered text with larger font
            self.center_text(" ", 727.0, font_size=70)
            
            self.master.resizable(False, False)
        
        # Ensure the canvas is displayed
        self.canvas.place(x=0, y=0)
        self.is_visible = True


class GUI2(GUIAdapter):
    """Adapter for gui2.py (Scene 3 - Camera recorder)"""
    def __init__(self, master=None):
        super().__init__(master)
        
    def setup(self):
        if self.master is None:
            self.master = tk.Tk()
        if self.canvas is None:
            # For 90 degree rotation, swap width and height
            if self.rotated:
                width = 1080
                height = 720
                canvas_width = width
            else:
                width = 720
                height = 1080
                canvas_width = width
                
            # Center the window on the screen
            self.master.update_idletasks()
            x = (self.master.winfo_screenwidth() // 2) - (width // 2)
            y = (self.master.winfo_screenheight() // 2) - (height // 2)
            self.master.geometry(f"{width}x{height}+{x}+{y}")
            self.master.configure(bg="#000000")
            
            # Create the canvas with rotated dimensions
            self.canvas = Canvas(
                self.master,
                bg="#000000",
                height=height,
                width=width,
                bd=0,
                highlightthickness=0,
                relief="ridge"
            )
            
            # Get the exact center of the canvas
            canvas_center_x = canvas_width / 2
            
            if self.rotated:
                # For rotated view, adjust the rectangle position
                rect_width = 494
                rect_height = 494
                
                # In rotated view, swap coordinates
                rect_left = height / 2 - rect_height / 2  # Center vertically in rotated view
                rect_right = height / 2 + rect_height / 2
                rect_top = width / 2 - rect_width / 2  # Center horizontally in rotated view
                rect_bottom = width / 2 + rect_width / 2
                
                self.canvas.create_rectangle(
                    rect_left,
                    rect_top,
                    rect_right,
                    rect_bottom,
                    fill="#92FBFF",
                    outline=""
                )
            else:
                # Standard non-rotated display
                rect_width = 494  # 607 - 113
                rect_height = 494  # 636 - 142
                rect_left = canvas_center_x - (rect_width / 2)
                rect_right = canvas_center_x + (rect_width / 2)
                rect_top = 293  # Center vertically (1080/2 - rect_height/2)
                rect_bottom = rect_top + rect_height
                
                self.canvas.create_rectangle(
                    rect_left,
                    rect_top,
                    rect_right,
                    rect_bottom,
                    fill="#92FBFF",
                    outline=""
                )
            
            # Set the assets path
            script_dir = Path(__file__).parent
            assets_path = script_dir / "assets" / "frame2"
            
            # Load image
            try:
                image_path = assets_path / "image_1.png"
                
                if self.rotated:
                    # Load with PIL to rotate
                    pil_image = Image.open(str(image_path))
                    pil_image = pil_image.rotate(90, expand=True)  # Rotate 90 degrees left
                    image = ImageTk.PhotoImage(pil_image)
                    self.assets["image_1.png"] = image
                    
                    # Place the rotated image at the center
                    self.canvas.create_image(
                        width / 2,  # Center horizontally in rotated view
                        height / 2,  # Center vertically in rotated view
                        image=image,
                        anchor="center"
                    )
                else:
                    # Standard non-rotated display
                    image = PhotoImage(file=str(image_path))
                    self.assets["image_1.png"] = image
                    
                    # Place the image exactly at the center of the canvas
                    self.canvas.create_image(
                        canvas_center_x,  # Exactly centered horizontally
                        540,  # Center of the screen vertically (1080/2)
                        image=image,
                        anchor="center"  # Important: use center anchor for proper centering
                    )
            except Exception as e:
                print(f"Error loading image: {e}")
            
            # Add centered text with larger font
            self.center_text(" ", 749.0, font_size=70)
            
            self.master.resizable(False, False)
        
        # Ensure the canvas is displayed
        self.canvas.place(x=0, y=0)
        self.is_visible = True