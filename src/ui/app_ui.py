import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os
from PIL import Image, ImageTk
import math

class RoundedButton(tk.Canvas):
    """A modern rounded button with hover and click effects"""
    def __init__(self, parent, text, command=None, width=120, height=40, 
                 color="#3B82F6", text_color="white", font=("Helvetica", 12),
                 corner_radius=20, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bg=parent["bg"], **kwargs)
        
        self.command = command
        self.color = color
        self.text_color = text_color
        self.font = font
        self.corner_radius = corner_radius
        self.pressed = False
        
        # Create the button rectangle
        self.rect_id = self.create_rounded_rect(0, 0, width, height, corner_radius, 
                                              fill=color)
        
        # Create the text
        self.text_id = self.create_text(width//2, height//2, text=text,
                                      fill=text_color, font=font)
        
        # Bind events
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle on the canvas"""
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def _on_press(self, event):
        self.pressed = True
        # Create a darker color for the "pressed" state
        darker_color = self._adjust_color_brightness(self.color, -30)
        
        # Create a pressing animation - scale slightly and darken
        self.itemconfig(self.rect_id, fill=darker_color)
        self.scale(self.rect_id, self.winfo_width()/2, self.winfo_height()/2, 0.96, 0.96)
        self.scale(self.text_id, self.winfo_width()/2, self.winfo_height()/2, 0.96, 0.96)
        
        # Add subtle shadow effect
        self.move(self.rect_id, 1, 1)
        self.move(self.text_id, 1, 1)
    
    def _on_release(self, event):
        if self.pressed:
            self.pressed = False
            # Reset animation
            self.itemconfig(self.rect_id, fill=self.color)
            self.scale(self.rect_id, self.winfo_width()/2, self.winfo_height()/2, 1.042, 1.042)
            self.scale(self.text_id, self.winfo_width()/2, self.winfo_height()/2, 1.042, 1.042)
            
            # Reset position
            self.move(self.rect_id, -1, -1)
            self.move(self.text_id, -1, -1)
            
            # Execute the command
            if self.command:
                self.command()
    
    def _on_enter(self, event):
        # Create a lighter color for hover state
        lighter_color = self._adjust_color_brightness(self.color, 20)
        
        # Subtle grow effect on hover
        self.itemconfig(self.rect_id, fill=lighter_color)
        
        # Scale up slightly for hover effect
        self.scale(self.rect_id, self.winfo_width()/2, self.winfo_height()/2, 1.03, 1.03)
        self.scale(self.text_id, self.winfo_width()/2, self.winfo_height()/2, 1.03, 1.03)
    
    def _on_leave(self, event):
        self.pressed = False
        
        # Reset color and scale
        self.itemconfig(self.rect_id, fill=self.color)
        self.scale(self.rect_id, self.winfo_width()/2, self.winfo_height()/2, 0.97, 0.97)
        self.scale(self.text_id, self.winfo_width()/2, self.winfo_height()/2, 0.97, 0.97)
        
        # Reset text position if still pressed when mouse leaves
        self.coords(self.text_id, self.winfo_width() // 2, self.winfo_height() // 2)
    
    def _adjust_color_brightness(self, color, amount):
        # Convert hex to RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Adjust brightness
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

class ModernToggle(tk.Canvas):
    """Modern toggle switch for language selection"""
    def __init__(self, parent, width=60, height=30, initial_state=False, on_color="#3B82F6", off_color="#CBD5E1", 
                 callback=None, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, 
                        bg=parent["bg"], **kwargs)
        self.on_color = on_color
        self.off_color = off_color
        self.state = initial_state
        self.callback = callback
        
        # Track animation state
        self.animating = False
        self.animation_steps = 10
        self.current_step = 0
        
        # Draw background
        self.bg_id = self.create_rounded_rect(0, 0, width, height, height//2, 
                                           fill=on_color if initial_state else off_color)
        
        # Draw toggle knob
        knob_margin = 2
        knob_size = height - 2*knob_margin
        knob_x = width - knob_size - knob_margin if initial_state else knob_margin
        self.knob_id = self.create_oval(knob_x, knob_margin, 
                                      knob_x + knob_size, knob_size + knob_margin, 
                                      fill="white", outline="")
        
        # Shadow effect for knob
        shadow_offset = 1
        self.shadow_id = self.create_oval(knob_x + shadow_offset, knob_margin + shadow_offset, 
                                       knob_x + knob_size + shadow_offset, knob_size + knob_margin + shadow_offset, 
                                       fill="#00000022", outline="")
        self.tag_lower(self.shadow_id, self.knob_id)
        
        # Bind events
        self.bind("<ButtonPress-1>", self.toggle)
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle on the canvas"""
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
        
    def toggle(self, event=None):
        """Toggle the switch state with animation"""
        if self.animating:
            return
            
        self.state = not self.state
        self.animating = True
        self.current_step = 0
        
        # Calculate total movement distance
        knob_margin = 2
        knob_size = self.winfo_height() - 2*knob_margin
        knob_x_start = self.coords(self.knob_id)[0]
        knob_x_end = self.winfo_width() - knob_size - knob_margin if self.state else knob_margin
        distance_per_step = (knob_x_end - knob_x_start) / self.animation_steps
        
        # Start the animation
        self._animate_toggle(knob_x_start, distance_per_step)
        
    def _animate_toggle(self, start_x, distance_per_step):
        """Animate the toggle movement"""
        if self.current_step >= self.animation_steps:
            self.animating = False
            # Execute the callback at the end of animation
            if self.callback:
                self.callback(self.state)
            return
            
        # Update color with gradient effect
        if self.state:
            # Transition from off to on color
            ratio = (self.current_step + 1) / self.animation_steps
            r = int(int(self.off_color[1:3], 16) * (1-ratio) + int(self.on_color[1:3], 16) * ratio)
            g = int(int(self.off_color[3:5], 16) * (1-ratio) + int(self.on_color[3:5], 16) * ratio)
            b = int(int(self.off_color[5:7], 16) * (1-ratio) + int(self.on_color[5:7], 16) * ratio)
        else:
            # Transition from on to off color
            ratio = (self.current_step + 1) / self.animation_steps
            r = int(int(self.on_color[1:3], 16) * (1-ratio) + int(self.off_color[1:3], 16) * ratio)
            g = int(int(self.on_color[3:5], 16) * (1-ratio) + int(self.on_color[3:5], 16) * ratio)
            b = int(int(self.on_color[5:7], 16) * (1-ratio) + int(self.off_color[5:7], 16) * ratio)
        
        color = f"#{r:02x}{g:02x}{b:02x}"
        self.itemconfig(self.bg_id, fill=color)
        
        # Move knob
        current_x = start_x + (self.current_step + 1) * distance_per_step
        current_coords = self.coords(self.knob_id)
        x_move = current_x - current_coords[0]
        self.move(self.knob_id, x_move, 0)
        self.move(self.shadow_id, x_move, 0)
        
        # Schedule next frame
        self.current_step += 1
        self.after(20, lambda: self._animate_toggle(start_x, distance_per_step))
    
    def _create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        # Create rounded rectangle
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def _on_press(self, event):
        self.pressed = True
        # Create a darker color for the "pressed" state
        darker_color = self._adjust_color_brightness(self.color, -30)
        
        # Create a pressing animation - scale slightly and darken
        self.itemconfig(self.rect_id, fill=darker_color)
        self.scale(self.rect_id, self.winfo_width()/2, self.winfo_height()/2, 0.96, 0.96)
        self.scale(self.text_id, self.winfo_width()/2, self.winfo_height()/2, 0.96, 0.96)
        
        # Add subtle shadow effect
        self.move(self.rect_id, 1, 1)
        self.move(self.text_id, 1, 1)
    
    def _on_release(self, event):
        if self.pressed:
            self.pressed = False
            # Reset animation
            self.itemconfig(self.rect_id, fill=self.color)
            self.scale(self.rect_id, self.winfo_width()/2, self.winfo_height()/2, 1.042, 1.042)
            self.scale(self.text_id, self.winfo_width()/2, self.winfo_height()/2, 1.042, 1.042)
            
            # Reset position
            self.move(self.rect_id, -1, -1)
            self.move(self.text_id, -1, -1)
            
            # Execute the command
            if self.command:
                self.command()
    
    def _on_enter(self, event):
        # Create a lighter color for hover state
        lighter_color = self._adjust_color_brightness(self.color, 20)
        
        # Subtle grow effect on hover
        self.itemconfig(self.rect_id, fill=lighter_color)
        
        # Scale up slightly for hover effect
        self.scale(self.rect_id, self.winfo_width()/2, self.winfo_height()/2, 1.03, 1.03)
        self.scale(self.text_id, self.winfo_width()/2, self.winfo_height()/2, 1.03, 1.03)
    
    def _on_leave(self, event):
        self.pressed = False
        
        # Reset color and scale
        self.itemconfig(self.rect_id, fill=self.color)
        self.scale(self.rect_id, self.winfo_width()/2, self.winfo_height()/2, 0.97, 0.97)
        self.scale(self.text_id, self.winfo_width()/2, self.winfo_height()/2, 0.97, 0.97)
        
        # Reset text position if still pressed when mouse leaves
        self.coords(self.text_id, self.winfo_width() // 2, self.winfo_height() // 2)
    
    def _adjust_color_brightness(self, color, amount):
        # Convert hex to RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Adjust brightness
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

class AppUI:
    def __init__(self, root, recognizer, translator, recorder):
        """Initialize the application UI"""
        self.root = root
        self.recognizer = recognizer
        self.translator = translator
        self.recorder = recorder
        
        # Configure the root window
        self.root.title("Speech Translator")
        self.root.geometry("900x650")
        self.root.minsize(900, 650)
        
        # Set color scheme (modern 2025 design)
        self.bg_color = "#F8F9FA"  # Light clean background
        self.accent_colors = {
            "primary": "#6366F1",  # Indigo
            "secondary": "#F43F5E",  # Rose/pink
            "success": "#10B981",  # Emerald green
            "info": "#3B82F6",  # Blue
            "warning": "#F59E0B",  # Amber
            "danger": "#EF4444"    # Red
        }
        self.text_color = "#1F2937"  # Dark gray
        self.root.configure(bg=self.bg_color)
        
        # Use a modern font
        try:
            self.font_family = "Helvetica Neue"  # Modern clean font
        except:
            self.font_family = "Helvetica"
        
        # Variables for language selection
        self.source_lang_var = tk.StringVar(value="en")
        self.target_lang_var = tk.StringVar(value="ru")
        
        # Variable for status messages
        self.status_var = tk.StringVar(value="Ready")
        
        # Get supported languages from recognizer
        self.supported_languages = self.recognizer.get_supported_languages()
        
        # Text variables
        self.source_text = ""
        self.translated_text = ""
        
        # Recording state
        self.is_recording = False
        
        # Animation variables
        self.animation_speed = 0.05  # seconds per frame
        self.animation_frames = []
        self.current_animation_frame = 0
        self.animation_running = False
        
    def setup_ui(self):
        """Set up the UI layout and widgets"""
        # Main container with subtle drop shadow
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Modern header with gradient effect
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=15)
        
        # Create a modern logo using canvas
        logo_size = 50
        logo_canvas = tk.Canvas(header_frame, width=logo_size, height=logo_size, 
                               bg=self.bg_color, highlightthickness=0)
        logo_canvas.pack(side=tk.LEFT, padx=15)
        
        # Draw a modern circular logo with gradient effect
        gradient_colors = [self.accent_colors["primary"], self.accent_colors["info"]]
        for i in range(logo_size):
            # Create gradient effect
            ratio = i / logo_size
            r1 = int(int(gradient_colors[0][1:3], 16) * (1-ratio) + int(gradient_colors[1][1:3], 16) * ratio)
            g1 = int(int(gradient_colors[0][3:5], 16) * (1-ratio) + int(gradient_colors[1][3:5], 16) * ratio)
            b1 = int(int(gradient_colors[0][5:7], 16) * (1-ratio) + int(gradient_colors[1][5:7], 16) * ratio)
            color = f"#{r1:02x}{g1:02x}{b1:02x}"
            logo_canvas.create_oval(i/2, i/2, logo_size-i/2, logo_size-i/2, fill=color, outline="")
        
        # Add a sound wave icon in the center
        wave_points = []
        center_x, center_y = logo_size/2, logo_size/2
        for i in range(0, 360, 45):
            angle = math.radians(i)
            radius = 8 if i % 90 == 0 else 14
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            wave_points.extend([x, y])
        logo_canvas.create_polygon(wave_points, fill="white", smooth=True)
        
        # Add title with modern styling
        title_frame = tk.Frame(header_frame, bg=self.bg_color)
        title_frame.pack(side=tk.LEFT, padx=15)
        
        title_label = tk.Label(title_frame, text="Speech Translator", 
                              font=(self.font_family, 28, "bold"),
                              fg=self.accent_colors["primary"], bg=self.bg_color)
        title_label.pack(pady=5)
        
        # Modern subtitle with animated underline
        self.subtitle_label = tk.Label(title_frame, text="Real-time language translation", 
                                     font=(self.font_family, 14),
                                     fg=self.accent_colors["secondary"], bg=self.bg_color)
        self.subtitle_label.pack()
        
        # Create a modern animated underline for subtitle
        self.underline_canvas = tk.Canvas(title_frame, height=2, bg=self.bg_color, highlightthickness=0)
        self.underline_canvas.pack(fill=tk.X)
        self.underline_width = 0
        self.underline_growing = True
        self.animate_underline()
        
        # Modern language selection frame with glass morphism effect
        lang_frame = tk.Frame(main_frame, bg=self.bg_color, pady=15)
        lang_frame.pack(fill=tk.X)
        
        # Source language panel - glass morphism style
        source_frame = tk.Frame(lang_frame, bg=self.bg_color, padx=15, pady=15,
                              highlightbackground=self.accent_colors["info"],
                              highlightthickness=1, bd=0)
        source_frame.pack(side=tk.LEFT, padx=15, fill=tk.X, expand=True)
        
        # Add modern header with icon
        source_header_frame = tk.Frame(source_frame, bg=self.bg_color)
        source_header_frame.pack(anchor=tk.W, pady=(0, 10))
        
        # Icon for speech
        icon_canvas = tk.Canvas(source_header_frame, width=24, height=24, 
                               bg=self.bg_color, highlightthickness=0)
        icon_canvas.pack(side=tk.LEFT)
        # Draw microphone icon
        icon_canvas.create_oval(5, 5, 19, 19, fill=self.accent_colors["info"], outline="")
        icon_canvas.create_rectangle(10, 3, 14, 15, fill=self.accent_colors["info"], outline="")
        
        source_header = tk.Label(source_header_frame, text="Speech Language", 
                               font=(self.font_family, 16, "bold"),
                               fg=self.accent_colors["info"], bg=self.bg_color)
        source_header.pack(side=tk.LEFT, padx=5)
        
        lang_options = [
            (code, name) for code, name in self.supported_languages.items()
        ]
        
        # Create cartoon-style radio buttons for language selection
        for code, name in lang_options:
            btn_frame = tk.Frame(source_frame, bg=self.bg_color)
            btn_frame.pack(anchor=tk.W, pady=5)
            
            # Create a custom radio button (a colored circle with label)
            radio_canvas = tk.Canvas(btn_frame, width=20, height=20, bg=self.bg_color, highlightthickness=0)
            radio_canvas.pack(side=tk.LEFT)
            
            # Draw the outer circle
            outer_circle = radio_canvas.create_oval(2, 2, 18, 18, 
                                                 outline=self.accent_colors["info"], width=2)
            
            # Draw the inner circle (filled when selected)
            inner_circle = radio_canvas.create_oval(6, 6, 14, 14, 
                                                 fill="" if self.source_lang_var.get() != code 
                                                 else self.accent_colors["info"],
                                                 outline="")
            
            # Store circles and code for later updates
            radio_canvas.circles = (outer_circle, inner_circle, code)
            
            # Language label
            lang_label = tk.Label(btn_frame, text=name, 
                                font=(self.font_family, 12),
                                fg=self.text_color, bg=self.bg_color)
            lang_label.pack(side=tk.LEFT, padx=5)
            
            # Set up the callback when clicking anywhere in the frame
            btn_frame.bind("<Button-1>", lambda e, canvas=radio_canvas: 
                         self._update_source_language(canvas.circles[2]))
            radio_canvas.bind("<Button-1>", lambda e, canvas=radio_canvas: 
                            self._update_source_language(canvas.circles[2]))
            lang_label.bind("<Button-1>", lambda e, canvas=radio_canvas: 
                          self._update_source_language(canvas.circles[2]))
            
            # Add hover effect
            for widget in (btn_frame, radio_canvas, lang_label):
                widget.bind("<Enter>", lambda e, l=lang_label: 
                          l.config(fg=self.accent_colors["info"]))
                widget.bind("<Leave>", lambda e, l=lang_label: 
                          l.config(fg=self.text_color))
        
        # Target language selection
        target_frame = tk.Frame(lang_frame, bg=self.bg_color, padx=10, pady=10,
                               highlightbackground=self.accent_colors["secondary"],
                               highlightthickness=2, bd=0)
        target_frame.pack(side=tk.RIGHT, padx=15, fill=tk.X, expand=True)
        
        # Add a decorative header
        target_header = tk.Label(target_frame, text="Translation Target", 
                                font=(self.font_family, 16, "bold"),
                                fg=self.accent_colors["secondary"], bg=self.bg_color)
        target_header.pack(pady=(0, 10))
        
        # Create cartoon-style radio buttons for target language selection
        for code, name in lang_options:
            if code != "ja":  # Only English and Russian as targets for simplicity
                btn_frame = tk.Frame(target_frame, bg=self.bg_color)
                btn_frame.pack(anchor=tk.W, pady=5)
                
                # Create a custom radio button
                radio_canvas = tk.Canvas(btn_frame, width=20, height=20, bg=self.bg_color, highlightthickness=0)
                radio_canvas.pack(side=tk.LEFT)
                
                # Draw the outer circle
                outer_circle = radio_canvas.create_oval(2, 2, 18, 18, 
                                                     outline=self.accent_colors["secondary"], width=2)
                
                # Draw the inner circle (filled when selected)
                inner_circle = radio_canvas.create_oval(6, 6, 14, 14, 
                                                     fill="" if self.target_lang_var.get() != code 
                                                     else self.accent_colors["secondary"],
                                                     outline="")
                
                # Store circles and code for later updates
                radio_canvas.circles = (outer_circle, inner_circle, code)
                
                # Language label
                lang_label = tk.Label(btn_frame, text=name, 
                                    font=(self.font_family, 12),
                                    fg=self.text_color, bg=self.bg_color)
                lang_label.pack(side=tk.LEFT, padx=5)
                
                # Set up the callback when clicking anywhere in the frame
                btn_frame.bind("<Button-1>", lambda e, canvas=radio_canvas: 
                             self._update_target_language(canvas.circles[2]))
                radio_canvas.bind("<Button-1>", lambda e, canvas=radio_canvas: 
                                self._update_target_language(canvas.circles[2]))
                lang_label.bind("<Button-1>", lambda e, canvas=radio_canvas: 
                              self._update_target_language(canvas.circles[2]))
                
                # Add hover effect
                for widget in (btn_frame, radio_canvas, lang_label):
                    widget.bind("<Enter>", lambda e, l=lang_label: 
                              l.config(fg=self.accent_colors["secondary"]))
                    widget.bind("<Leave>", lambda e, l=lang_label: 
                              l.config(fg=self.text_color))
        
        # Action buttons frame with modern styling and fixed positions
        action_frame = tk.Frame(main_frame, bg=self.bg_color)
        action_frame.pack(fill=tk.X, pady=15)
        
        # Left button container
        left_btn_frame = tk.Frame(action_frame, bg=self.bg_color)
        left_btn_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Right button container
        right_btn_frame = tk.Frame(action_frame, bg=self.bg_color)
        right_btn_frame.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        
        # Speech recognition button - modern style with icon
        self.speech_button = RoundedButton(
            left_btn_frame, 
            width=150, 
            height=50, 
            corner_radius=25,  # Fully rounded corners
            color=self.accent_colors["primary"],
            text="Speech to Text", 
            command=self._speech_to_text
        )
        self.speech_button.pack(side=tk.LEFT, padx=15)
        
        # Translate button - modern style
        self.translate_button = RoundedButton(
            left_btn_frame, 
            width=150, 
            height=50, 
            corner_radius=25,
            color=self.accent_colors["success"],
            text="Translate", 
            command=self._translate_text
        )
        self.translate_button.pack(side=tk.LEFT, padx=15)
        
        # Video recording button - modern style
        self.record_button = RoundedButton(
            right_btn_frame, 
            width=150, 
            height=50, 
            corner_radius=25,
            color=self.accent_colors["danger"],
            text="Start Recording", 
            command=self._toggle_recording
        )
        self.record_button.pack(side=tk.RIGHT, padx=15)
        
        # Clear button - modern style with fixed position
        self.clear_button = RoundedButton(
            right_btn_frame, 
            width=150, 
            height=50, 
            corner_radius=25,
            color=self.accent_colors["warning"],
            text="Clear", 
            command=self._clear_text
        )
        self.clear_button.pack(side=tk.RIGHT, padx=15)
        
        # Text areas frame with modern styling
        text_frame = tk.Frame(main_frame, bg=self.bg_color)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Source text area with modern glass morphism styling
        source_text_frame = tk.Frame(text_frame, bg=self.bg_color, padx=15, pady=15,
                                   highlightbackground=self.accent_colors["info"],
                                   highlightthickness=1, bd=0)
        source_text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15)
        
        # Modern header with icon
        source_text_header_frame = tk.Frame(source_text_frame, bg=self.bg_color)
        source_text_header_frame.pack(anchor=tk.W, pady=(0, 10))
        
        # Icon for source text
        source_icon = tk.Canvas(source_text_header_frame, width=24, height=24, 
                             bg=self.bg_color, highlightthickness=0)
        source_icon.pack(side=tk.LEFT)
        source_icon.create_oval(2, 2, 22, 22, fill=self.accent_colors["info"], outline="")
        source_icon.create_text(12, 12, text="A", fill="white", font=(self.font_family, 12, "bold"))
        
        source_header = tk.Label(source_text_header_frame, text="Source Text", 
                              font=(self.font_family, 14, "bold"),
                              fg=self.accent_colors["info"], bg=self.bg_color)
        source_header.pack(side=tk.LEFT, padx=5)
        
        # Modern text area with rounded corners and subtle shadow
        self.source_text_area = scrolledtext.ScrolledText(
            source_text_frame, 
            wrap=tk.WORD,
            width=40, 
            height=12,
            font=(self.font_family, 12),
            bg="#FFFFFF",
            fg=self.text_color,
            insertbackground=self.accent_colors["info"],  # Cursor color
            selectbackground=self.accent_colors["info"],  # Selection color
            selectforeground="#FFFFFF",
            padx=10,
            pady=10,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#E2E8F0"  # Subtle border
        )
        self.source_text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Translated text area with modern glass morphism styling
        target_text_frame = tk.Frame(text_frame, bg=self.bg_color, padx=15, pady=15,
                                   highlightbackground=self.accent_colors["secondary"],
                                   highlightthickness=1, bd=0)
        target_text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=15)
        
        # Modern header with icon for target
        target_text_header_frame = tk.Frame(target_text_frame, bg=self.bg_color)
        target_text_header_frame.pack(anchor=tk.W, pady=(0, 10))
        
        # Icon for target text
        target_icon = tk.Canvas(target_text_header_frame, width=24, height=24, 
                              bg=self.bg_color, highlightthickness=0)
        target_icon.pack(side=tk.LEFT)
        target_icon.create_oval(2, 2, 22, 22, fill=self.accent_colors["secondary"], outline="")
        target_icon.create_text(12, 12, text="B", fill="white", font=(self.font_family, 12, "bold"))
        
        target_header = tk.Label(target_text_header_frame, text="Translated Text", 
                               font=(self.font_family, 14, "bold"),
                               fg=self.accent_colors["secondary"], bg=self.bg_color)
        target_header.pack(side=tk.LEFT, padx=5)
        
        self.target_text_area = scrolledtext.ScrolledText(
            target_text_frame, 
            wrap=tk.WORD,
            width=40, 
            height=12,
            font=(self.font_family, 12),
            bg="#FFFFFF",
            fg=self.text_color,
            insertbackground=self.accent_colors["secondary"],  # Cursor color
            selectbackground=self.accent_colors["secondary"],  # Selection color
            selectforeground="#FFFFFF",
            padx=10,
            pady=10,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#E2E8F0"  # Subtle border
        )
        self.target_text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Modern style status bar with gradient effect
        status_frame = tk.Frame(main_frame, bg=self.bg_color, pady=10)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        status_height = 36
        status_canvas = tk.Canvas(status_frame, height=status_height, bg=self.bg_color, 
                                highlightthickness=0)
        status_canvas.pack(fill=tk.X)
        
        # Create a modern rounded rectangle with gradient for the status bar
        def create_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
            points = [
                x1+radius, y1,
                x2-radius, y1,
                x2, y1,
                x2, y1+radius,
                x2, y2-radius,
                x2, y2,
                x2-radius, y2,
                x1+radius, y2,
                x1, y2,
                x1, y2-radius,
                x1, y1+radius,
                x1, y1
            ]
            return canvas.create_polygon(points, smooth=True, **kwargs)
        
        # Create gradient background for status bar
        bg_colors = ["#F8FAFC", "#E2E8F0"]
        for i in range(status_height):
            ratio = i / status_height
            r = int(int(bg_colors[0][1:3], 16) * (1-ratio) + int(bg_colors[1][1:3], 16) * ratio)
            g = int(int(bg_colors[0][3:5], 16) * (1-ratio) + int(bg_colors[1][3:5], 16) * ratio)
            b = int(int(bg_colors[0][5:7], 16) * (1-ratio) + int(bg_colors[1][5:7], 16) * ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            status_canvas.create_line(0, i, status_canvas.winfo_reqwidth(), i, fill=color)
        
        status_bg = create_rounded_rect(
            status_canvas, 0, 0, status_canvas.winfo_reqwidth(), status_height, 10,
            fill="", outline=self.accent_colors["primary"], width=1)
        
        # Status icon
        status_icon = tk.Canvas(status_canvas, width=20, height=20, 
                             bg=bg_colors[1], highlightthickness=0)
        status_icon.place(x=12, y=8)
        status_icon.create_oval(0, 0, 20, 20, fill=self.accent_colors["primary"], outline="")
        status_icon.create_text(10, 10, text="i", fill="white", font=(self.font_family, 10, "bold"))
        
        # Modern status text
        self.status_label = tk.Label(status_canvas, textvariable=self.status_var,
                                   font=(self.font_family, 11),
                                   fg=self.text_color, bg=bg_colors[1])
        self.status_label.place(x=40, y=8)
        
        # Make the canvas resize with the window
        def resize_status_bar(event=None):
            status_canvas.delete(status_bg)
            # Redraw gradient
            status_canvas.delete("all")
            for i in range(status_height):
                ratio = i / status_height
                r = int(int(bg_colors[0][1:3], 16) * (1-ratio) + int(bg_colors[1][1:3], 16) * ratio)
                g = int(int(bg_colors[0][3:5], 16) * (1-ratio) + int(bg_colors[1][3:5], 16) * ratio)
                b = int(int(bg_colors[0][5:7], 16) * (1-ratio) + int(bg_colors[1][5:7], 16) * ratio)
                color = f"#{r:02x}{g:02x}{b:02x}"
                status_canvas.create_line(0, i, status_canvas.winfo_width(), i, fill=color)
            
            # Redraw rounded rectangle
            new_rect = create_rounded_rect(
                status_canvas, 0, 0, status_canvas.winfo_width(), status_height, 10,
                fill="", outline=self.accent_colors["primary"], width=1)
            status_canvas.tag_lower(new_rect)
            
            # Reposition status icon and label
            status_icon.place(x=12, y=8)
            self.status_label.place(x=40, y=8)
        
        self.root.bind("<Configure>", resize_status_bar)
        
        # Initialize the UI layout
        resize_status_bar()
    
    def _resize_status_bar(self, canvas, rectangle):
        """Resize the status bar when the window is resized"""
        canvas.delete(rectangle)
        new_rect = canvas.create_rounded_rect(
            0, 0, canvas.winfo_width(), 30, 10, 
            fill="#E6E9ED", outline="")
        canvas.tag_lower(new_rect)  # Put it behind the text
    
    def animate_underline(self):
        """Animate the underline for subtitle with growing/shrinking effect"""
        max_width = self.subtitle_label.winfo_width() - 10
        
        # Clear previous line
        self.underline_canvas.delete("all")
        
        # Update width according to direction
        if self.underline_growing:
            self.underline_width += 3
            if self.underline_width >= max_width:
                self.underline_width = max_width
                self.underline_growing = False
        else:
            self.underline_width -= 3
            if self.underline_width <= 0:
                self.underline_width = 0
                self.underline_growing = True
        
        # Create gradient line
        if self.underline_width > 0:
            # Create gradient from primary to secondary color
            for i in range(self.underline_width):
                ratio = i / self.underline_width
                r1 = int(int(self.accent_colors["primary"][1:3], 16) * (1-ratio) + 
                         int(self.accent_colors["secondary"][1:3], 16) * ratio)
                g1 = int(int(self.accent_colors["primary"][3:5], 16) * (1-ratio) + 
                         int(self.accent_colors["secondary"][3:5], 16) * ratio)
                b1 = int(int(self.accent_colors["primary"][5:7], 16) * (1-ratio) + 
                         int(self.accent_colors["secondary"][5:7], 16) * ratio)
                color = f"#{r1:02x}{g1:02x}{b1:02x}"
                self.underline_canvas.create_line(i, 1, i+1, 1, fill=color, width=2)
        
        # Schedule next frame
        self.root.after(30, self.animate_underline)
    
    def _setup_bouncing_text(self, label):
        """Set up a bouncing animation for a label"""
        self.bounce_offset = 0
        self.bounce_direction = 1
        self.max_bounce = 3
    
    def _animate_bouncing_text(self):
        """Animate the bouncing text effect"""
        if hasattr(self, 'bounce_offset'):
            # Update the bounce position
            self.bounce_offset += 0.5 * self.bounce_direction
            
            # Reverse direction at the extremes
            if abs(self.bounce_offset) >= self.max_bounce:
                self.bounce_direction *= -1
            
            # Apply the new position
            self.subtitle_label.place(y=self.bounce_offset)
            
            # Schedule the next frame
            self.root.after(50, self._animate_bouncing_text)
    
    def _update_source_language(self, language_code):
        """Update the source language selection"""
        self.source_lang_var.set(language_code)
        
        # Update all radio buttons
        for widget in self.root.winfo_children():
            self._update_radio_buttons(widget, "source", language_code)
        
        # Update the recognizer
        self.recognizer.set_language(language_code)
        self.status_var.set(f"Speech recognition language set to {self.supported_languages[language_code]}")
    
    def _update_target_language(self, language_code):
        """Update the target language selection"""
        self.target_lang_var.set(language_code)
        
        # Update all radio buttons
        for widget in self.root.winfo_children():
            self._update_radio_buttons(widget, "target", language_code)
        
        # Update the translator
        self.translator.set_target_language(language_code)
        self.status_var.set(f"Translation language set to {self.supported_languages[language_code]}")
    
    def _update_radio_buttons(self, widget, button_type, selected_code):
        """Recursively update radio buttons in the interface"""
        if hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                self._update_radio_buttons(child, button_type, selected_code)
        
        if isinstance(widget, tk.Canvas) and hasattr(widget, 'circles'):
            outer_circle, inner_circle, code = widget.circles
            
            # Check if this is a source or target language button
            is_source = button_type == "source" and code in self.source_lang_var.get()
            is_target = button_type == "target" and code in self.target_lang_var.get()
            
            if is_source or is_target:
                # Selected state - fill the inner circle
                fill_color = self.accent_colors["info"] if is_source else self.accent_colors["secondary"]
                widget.itemconfig(inner_circle, fill=fill_color)
            elif code == selected_code:
                # Selected state - fill the inner circle
                fill_color = self.accent_colors["info"] if button_type == "source" else self.accent_colors["secondary"]
                widget.itemconfig(inner_circle, fill=fill_color)
            else:
                # Unselected state - empty the inner circle
                widget.itemconfig(inner_circle, fill="")
    
    def _speech_to_text(self):
        """Start speech recognition in a separate thread"""
        def speech_thread():
            # Disable the button and update status with animation
            self.speech_button.itemconfig(1, fill=self.accent_colors["info"])  # Button color change
            self._pulse_status("Listening... Speak now")
            
            try:
                # Get speech input
                text = self.recognizer.recognize_speech()
                
                if text:
                    # Update the source text area with a typewriter effect
                    self._typewriter_effect(self.source_text_area, text)
                    self.source_text = text
                    
                    # Auto-translate if we have text
                    self._translate_text()
                    
                    self.status_var.set("Speech recognized successfully! 🎉")
                else:
                    self._shake_widget(self.speech_button)
                    self.status_var.set("Could not recognize speech 🤔")
            except Exception as e:
                self._shake_widget(self.speech_button)
                self.status_var.set(f"Error: {str(e)} 😕")
                messagebox.showerror("Speech Recognition Error", str(e))
            finally:
                # Reset button color
                self.speech_button.itemconfig(1, fill=self.accent_colors["primary"])
        
        # Start in a separate thread to keep UI responsive
        threading.Thread(target=speech_thread, daemon=True).start()
    
    def _translate_text(self):
        """Translate the text in the source text area"""
        # Get the text from the source area
        source_text = self.source_text_area.get(1.0, tk.END).strip()
        
        if not source_text:
            self._shake_widget(self.translate_button)
            self.status_var.set("No text to translate 📝")
            return
            
        self._pulse_status("Translating... ⏳")
        self.translate_button.itemconfig(1, fill=self.accent_colors["info"])  # Change button color during process
        
        def translate_thread():
            try:
                # Get source and target languages
                source_lang = self.source_lang_var.get()
                target_lang = self.target_lang_var.get()
                
                # Translate the text
                translated_text = self.translator.translate(
                    source_text, source_lang, target_lang
                )
                
                # Clear the target text area
                self.target_text_area.delete(1.0, tk.END)
                
                # Add the translated text with a typewriter effect
                self._typewriter_effect(self.target_text_area, translated_text)
                self.translated_text = translated_text
                
                self.status_var.set("Translation complete! 🌍")
            except Exception as e:
                self._shake_widget(self.translate_button)
                self.status_var.set(f"Translation error: {str(e)} ❌")
                messagebox.showerror("Translation Error", str(e))
            finally:
                # Reset button color
                self.translate_button.itemconfig(1, fill=self.accent_colors["success"])
        
        # Start in a separate thread to keep UI responsive
        threading.Thread(target=translate_thread, daemon=True).start()
    
    def _toggle_recording(self):
        """Toggle video recording on/off"""
        if not self.is_recording:
            # Start recording with animation
            success = self.recorder.start_recording()
            if success:
                self.is_recording = True
                self.record_button.itemconfig(2, text="Stop Recording")  # Update button text
                self.record_button.itemconfig(1, fill=self.accent_colors["danger"])  # Change color to active
                
                # Pulsing status animation
                self._pulse_status("Recording video... Press 'q' in video window to stop 📹")
                
                # Start a simple pulsing animation for the record button
                self._pulse_record_button()
        else:
            # Stop recording
            file_path = self.recorder.stop_recording()
            self.is_recording = False
            self.record_button.itemconfig(2, text="Start Recording")  # Reset button text
            self.record_button.itemconfig(1, fill=self.accent_colors["danger"])  # Reset color
            
            if file_path:
                self.status_var.set(f"Video saved! 🎬")
                
                # Create custom message box with cartoon styling
                dialog = tk.Toplevel(self.root)
                dialog.title("Recording Saved")
                dialog.geometry("400x200")
                dialog.configure(bg=self.bg_color)
                
                # Rounded frame for the dialog
                dialog_frame = tk.Frame(dialog, bg=self.bg_color, padx=20, pady=20,
                                      highlightbackground=self.accent_colors["success"],
                                      highlightthickness=2)
                dialog_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Message with cartoon styling
                message = tk.Label(dialog_frame, 
                                 text=f"Video saved successfully! 🎉\n\nLocation: {file_path}",
                                 font=(self.font_family, 12),
                                 bg=self.bg_color, fg=self.text_color,
                                 justify=tk.LEFT, wraplength=350)
                message.pack(pady=10)
                
                # Buttons container
                btn_frame = tk.Frame(dialog_frame, bg=self.bg_color)
                btn_frame.pack(pady=10)
                
                # Open folder button
                open_btn = RoundedButton(btn_frame, width=120, height=40, corner_radius=15,
                                       color=self.accent_colors["primary"], text="Open Folder",
                                       command=lambda: [os.system(f"open {os.path.dirname(file_path)}"), dialog.destroy()])
                open_btn.pack(side=tk.LEFT, padx=10)
                
                # Close button
                close_btn = RoundedButton(btn_frame, width=120, height=40, corner_radius=15,
                                        color=self.accent_colors["secondary"], text="Close",
                                        command=dialog.destroy)
                close_btn.pack(side=tk.LEFT, padx=10)
                
                # Center the dialog on the main window
                dialog.transient(self.root)
                dialog.grab_set()
                dialog.update_idletasks()
                x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
                y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
                dialog.geometry(f"+{x}+{y}")
    
    def _clear_text(self):
        """Clear all text areas with a modern fade animation"""
        # Store the original z-index of the clear button to restore it later
        original_z = self.clear_button.winfo_toplevel()
        
        # Ensure the button stays on top during animation
        self.clear_button.lift()
        
        # Flash button with a color change instead of bouncing
        original_color = self.clear_button.color
        flash_color = self.accent_colors["primary"]
        
        # Change button color for visual feedback
        self.clear_button.itemconfig(self.clear_button.rect_id, fill=flash_color)
        
        # Animate clearing of source text
        self._wipe_text(self.source_text_area)
        
        # Animate clearing of target text
        self._wipe_text(self.target_text_area)
        
        self.source_text = ""
        self.translated_text = ""
        self.status_var.set("Text cleared! ✨")
        
        # Reset button color after a short delay
        self.root.after(300, lambda: self.clear_button.itemconfig(
            self.clear_button.rect_id, fill=original_color))
    
    def _typewriter_effect(self, text_widget, text, delay=10):
        """Add text to a widget with a typewriter effect"""
        text_widget.delete(1.0, tk.END)
        
        def _type_char(index=0):
            if index < len(text):
                text_widget.insert(tk.END, text[index])
                text_widget.see(tk.END)  # Scroll to the end
                text_widget.master.after(delay, _type_char, index + 1)
        
        _type_char()
    
    def _wipe_text(self, text_widget):
        """Clear text with a wipe animation"""
        text = text_widget.get(1.0, tk.END)
        if text.strip():
            text_widget.delete(1.0, tk.END)
            text_widget.update()
    
    def _pulse_status(self, message):
        """Animate the status message with a pulsing effect"""
        colors = [self.text_color, self.accent_colors["primary"], self.accent_colors["info"]]
        self.status_var.set(message)
        
        def _pulse(index=0):
            if self.status_label.winfo_exists():  # Check if widget still exists
                self.status_label.config(fg=colors[index % len(colors)])
                self.status_label.after(300, _pulse, (index + 1) % len(colors))
        
        _pulse()
    
    def _pulse_record_button(self):
        """Create a pulsing animation for the record button while recording"""
        if self.is_recording and self.record_button.winfo_exists():
            # Toggle between two colors
            current_color = self.record_button.itemcget(1, "fill")
            new_color = self.accent_colors["warning"] if current_color == self.accent_colors["danger"] else self.accent_colors["danger"]
            
            self.record_button.itemconfig(1, fill=new_color)
            
            # Schedule the next pulse
            self.root.after(500, self._pulse_record_button)
    
    def _shake_widget(self, widget, amplitude=5, repeat=5):
        """Make a widget shake from side to side"""
        original_x = widget.winfo_x()
        
        def _shake_step(count=0):
            if count >= repeat * 2:
                # Reset position and exit
                widget.place(x=original_x)
                return
            
            # Calculate offset (alternating left and right)
            offset = amplitude if count % 2 == 0 else -amplitude
            widget.place(x=original_x + offset)
            
            # Schedule next shake
            widget.after(50, _shake_step, count + 1)
        
        _shake_step()
    
    def _bounce_widget(self, widget, amplitude=5, repeat=3):
        """Make a widget bounce up and down"""
        original_y = widget.winfo_y()
        
        def _bounce_step(count=0):
            if count >= repeat * 2:
                # Reset position and exit
                widget.place(y=original_y)
                return
            
            # Calculate offset (alternating up and down)
            offset = -amplitude if count % 2 == 0 else amplitude
            widget.place(y=original_y + offset)
            
            # Schedule next bounce
            widget.after(100, _bounce_step, count + 1)
        
        _bounce_step()