import cv2
import os
import time
import threading
from datetime import datetime

class Recorder:
    def __init__(self, output_dir='recordings'):
        """Initialize the video recorder with a directory for output files"""
        self.output_dir = output_dir
        self.is_recording = False
        self.video_capture = None
        self.record_thread = None
        self.current_output_file = None
        
        # Create the output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _generate_filename(self):
        """Generate a unique filename for the recording"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.output_dir, f"recording_{timestamp}.mp4")
    
    def _recording_thread(self):
        """Thread function for recording video"""
        try:
            # Set up video capture
            self.video_capture = cv2.VideoCapture(0)
            if not self.video_capture.isOpened():
                print("Error: Could not open video capture device")
                self.is_recording = False
                return
                
            # Get video properties
            width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = 20.0
            
            # Set up video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.current_output_file = self._generate_filename()
            out = cv2.VideoWriter(self.current_output_file, fourcc, fps, (width, height))
            
            # Recording loop
            while self.is_recording:
                ret, frame = self.video_capture.read()
                if ret:
                    # Write frame to video file
                    out.write(frame)
                    
                    # Display frame (flipped horizontally for mirror effect)
                    display_frame = cv2.flip(frame, 1)
                    cv2.putText(display_frame, "Recording", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.imshow("Video Recording", display_frame)
                    
                    # Check for exit key
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == 27:  # q or ESC
                        break
                else:
                    # Camera error or disconnected
                    print("Error: Failed to capture frame")
                    break
                    
                # Small delay to reduce CPU usage
                time.sleep(0.01)
            
            # Clean up
            out.release()
            
        except Exception as e:
            print(f"Recording error: {e}")
        finally:
            self.is_recording = False
            
    def start_recording(self):
        """Start recording video in a separate thread"""
        if self.is_recording:
            print("Already recording")
            return False
            
        self.is_recording = True
        self.record_thread = threading.Thread(target=self._recording_thread)
        self.record_thread.daemon = True
        self.record_thread.start()
        return True
        
    def stop_recording(self):
        """Stop the current recording"""
        if not self.is_recording:
            print("Not recording")
            return None
            
        self.is_recording = False
        if self.record_thread:
            self.record_thread.join(timeout=2.0)  # Wait for thread to finish
        
        # Return the path to the recorded file
        return self.current_output_file
        
    def is_recording_active(self):
        """Check if recording is currently active"""
        return self.is_recording
        
    def get_last_recording(self):
        """Get the path to the most recent recording"""
        return self.current_output_file