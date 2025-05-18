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
    
    def center_text(self, text, y, font_size=40, fill="#FFFFFF", font_family="Inter ExtraBold"):
        """Show centered text on the canvas"""
        if self.canvas:
            return self.canvas.create_text(
                360,  # Center x-coordinate for 720px wide canvas
                y,
                text=text,
                anchor="center",
                fill=fill,
                font=(font_family, font_size * -1)
            )
            
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
    """Adapter for gui.py (Scene 1 - Auto-detect to English)"""
    def __init__(self, master=None):
        super().__init__(master)
        
    def setup(self):
        if self.master is None:
            self.master = tk.Tk()
            
        if self.canvas is None:
            # Create the canvas only once
            self.master.geometry("720x1080")
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
            
            # Add centered text
            self.center_text("English", 711.0, font_size=70)
            
            self.master.resizable(False, False)
        
        # Ensure the canvas is displayed
        self.canvas.place(x=0, y=0)
        self.is_visible = True


class GUI1(GUIAdapter):
    """Adapter for gui1.py (Scene 2 - Auto-detect to Russian)"""
    def __init__(self, master=None):
        super().__init__(master)
        
    def setup(self):
        if self.master is None:
            self.master = tk.Tk()
            
        if self.canvas is None:
            # Create the canvas only once
            self.master.geometry("720x1080")
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
            
            # Add centered text
            self.center_text("Russian", 727.0, font_size=70)
            
            self.master.resizable(False, False)
        
        # Ensure the canvas is displayed
        self.canvas.place(x=0, y=0)
        self.is_visible = True


class GUI2(GUIAdapter):
    """Adapter for gui2.py (Scene 3 - Auto-detect to English with quick action)"""
    def __init__(self, master=None):
        super().__init__(master)
        
    def setup(self):
        if self.master is None:
            self.master = tk.Tk()
            
        if self.canvas is None:
            # Create the canvas only once
            self.master.geometry("720x1080")
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
            
            # Create centered background rectangle
            self.canvas.create_rectangle(
                113.0,
                142.0,
                607.0,  # These coordinates create a centered rectangle
                636.0,
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
                
                # Place the image at the center of the canvas
                self.canvas.create_image(
                    360.0,  # Centered horizontally (720/2)
                    383.0,
                    image=image
                )
            except Exception as e:
                print(f"Error loading image: {e}")
            
            # Add centered text
            self.center_text("Quick Mode", 749.0, font_size=70)
            
            self.master.resizable(False, False)
        
        # Ensure the canvas is displayed
        self.canvas.place(x=0, y=0)
        self.is_visible = True 