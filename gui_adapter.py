import os
import sys
import tkinter as tk
from tkinter import Canvas, PhotoImage
from pathlib import Path

class GUIAdapter:
    """Base adapter class for GUI files"""
    def __init__(self, master=None):
        self.master = master
        self.canvas = None
        self.assets = {}
        self.is_visible = False
        self.mirrored = True  # Enable mirroring by default for VR glasses
        
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
        """Show centered text on the canvas with simple mirroring for VR glasses"""
        if self.canvas:
            # Get canvas dimensions for proper centering
            canvas_width = self.canvas.winfo_width() or 720  # Default to 720 if not yet rendered
            canvas_height = self.canvas.winfo_height() or 1080  # Default to 1080 if not yet rendered
            canvas_center = canvas_width / 2
            
            # Make font size larger for better visibility
            scaled_font_size = int(font_size * 1.5)  # Make text 50% larger
            
            # Calculate y position as a percentage of screen height for better scaling
            y_percent = y / 1080  # Convert fixed y to percentage of reference height
            scaled_y = int(y_percent * canvas_height)  # Apply percentage to actual height
            
            # Create text with optional width constraint for wrapping
            kwargs = {
                "text": text,
                "anchor": "center",
                "fill": fill,
                "font": (font_family, scaled_font_size),
                "justify": "center"
            }
            
            # Add width parameter if provided (for text wrapping)
            if width:
                kwargs["width"] = width
                
            # If mirroring is enabled, reverse the text
            if self.mirrored:
                # Simple mirroring - just reverse the text
                mirrored_text = text[::-1]
                kwargs["text"] = mirrored_text
            
            # Create the text with a black outline for better visibility
            # First create a black shadow/outline
            outline_id = self.canvas.create_text(
                canvas_center,
                scaled_y,
                text=kwargs["text"],
                width=kwargs.get("width"),
                font=kwargs["font"],
                fill="black",
                anchor="center",
                justify="center"
            )
            
            # Move the outline slightly to create a shadow effect
            self.canvas.move(outline_id, 2, 2)
            
            # Then create the main text on top
            text_id = self.canvas.create_text(
                canvas_center,
                scaled_y,
                **kwargs
            )
            
            return text_id
            
    def show_transcription(self, text):
        """Show transcription text on a black background"""
        self.clear()
        # Create black background
        self.canvas.create_rectangle(0, 0, 720, 1080, fill="#000000", outline="")
        
        # Show the transcription text with word wrapping
        lines = []
        current_line = ""
        max_chars = 40  # Adjust based on your font size
        
        for word in text.split():
            if len(current_line + " " + word) <= max_chars:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
                
        if current_line:
            lines.append(current_line)
            
        y_pos = 400  # Start position
        for line in lines:
            self.center_text(line, y_pos, font_size=30)
            y_pos += 40


class GUI(GUIAdapter):
    """Adapter for gui.py (Scene 1 - Live Transcription)"""
    def __init__(self, master=None):
        super().__init__(master)
        
    def setup(self):
        if self.master is None:
            self.master = tk.Tk()
        if self.canvas is None:
            # Center the window on the screen
            self.master.update_idletasks()
            width = 720
            height = 1080
            x = (self.master.winfo_screenwidth() // 2) - (width // 2)
            y = (self.master.winfo_screenheight() // 2) - (height // 2)
            self.master.geometry(f"{width}x{height}+{x}+{y}")
            self.master.configure(bg="#000000")
            
            # Create the canvas
            self.canvas = Canvas(
                self.master,
                bg="#000000",
                height=1080,
                width=720,
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
            self.center_text("Live Transcription", 711.0, font_size=70)
            
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
            # Center the window on the screen
            self.master.update_idletasks()
            width = 720
            height = 1080
            x = (self.master.winfo_screenwidth() // 2) - (width // 2)
            y = (self.master.winfo_screenheight() // 2) - (height // 2)
            self.master.geometry(f"{width}x{height}+{x}+{y}")
            self.master.configure(bg="#000000")
            
            # Create the canvas
            self.canvas = Canvas(
                self.master,
                bg="#000000",
                height=1080,
                width=720,
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
            self.center_text("Russian Translation", 727.0, font_size=70)
            
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
            # Center the window on the screen
            self.master.update_idletasks()
            width = 720
            height = 1080
            x = (self.master.winfo_screenwidth() // 2) - (width // 2)
            y = (self.master.winfo_screenheight() // 2) - (height // 2)
            self.master.geometry(f"{width}x{height}+{x}+{y}")
            self.master.configure(bg="#000000")
            
            # Create the canvas
            self.canvas = Canvas(
                self.master,
                bg="#000000",
                height=1080,
                width=720,
                bd=0,
                highlightthickness=0,
                relief="ridge"
            )
            
            # Get the exact center of the canvas
            canvas_width = 720
            canvas_center_x = canvas_width / 2  # 360
            
            # Create perfectly centered background rectangle
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
            self.center_text("Camera Mode", 749.0, font_size=70)
            
            self.master.resizable(False, False)
        
        # Ensure the canvas is displayed
        self.canvas.place(x=0, y=0)
        self.is_visible = True