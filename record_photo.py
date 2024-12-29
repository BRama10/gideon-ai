import time
import os
from datetime import datetime
import subprocess
from threading import Event, Thread
import signal
from queue import Queue
import mss
import cv2
import numpy as np

class ScreenCapture:
    def __init__(self, output_folder, fps=20):
        self.output_folder = output_folder
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.stop_event = Event()
        self.frame_queue = Queue(maxsize=30)
        self.start_time = None
        self.capture_thread = None
        self.save_thread = None
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Initialize screen capture
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]  # Primary monitor
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        print("\nStopping capture...")
        self.stop_capture()

    def stop_capture(self):
        """Stop the capture process cleanly"""
        if not self.stop_event.is_set():
            print("Initiating stop sequence...")
            self.stop_event.set()
            
            if self.capture_thread and self.capture_thread.is_alive():
                print("Waiting for capture thread to finish...")
                self.capture_thread.join()
            
            if self.save_thread and self.save_thread.is_alive():
                print("Waiting for save thread to finish...")
                # Add remaining frames to queue
                while not self.frame_queue.empty():
                    self.frame_queue.get()
                self.save_thread.join()
            
            if hasattr(self, 'sct'):
                self.sct.close()
            print("Capture stopped successfully")
    
    def capture_screen(self):
        """Capture screen at specified intervals"""
        last_capture = 0
        
        while not self.stop_event.is_set():
            current_time = time.perf_counter()
            if current_time - last_capture >= self.frame_interval:
                try:
                    screenshot = self.sct.grab(self.monitor)
                    frame = np.array(screenshot)
                    rel_timestamp = time.perf_counter() - self.start_time
                    
                    if not self.frame_queue.full():
                        self.frame_queue.put((frame, rel_timestamp))
                    
                    last_capture = current_time
                except Exception as e:
                    print(f"Error capturing frame: {e}")
                    continue
            else:
                time.sleep(max(0, (self.frame_interval - (current_time - last_capture)) / 2))
    
    def save_frames(self):
        """Save frames from queue to disk"""
        while not (self.stop_event.is_set() and self.frame_queue.empty()):
            try:
                frame, timestamp = self.frame_queue.get(timeout=1)
                filename = f"frame_{timestamp:.3f}.jpg"
                filepath = os.path.join(self.output_folder, filename)
                
                cv2.imwrite(filepath, cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR),
                           [cv2.IMWRITE_JPEG_QUALITY, 95])
                
            except Queue.Empty:
                continue
            except Exception as e:
                if not isinstance(e, TimeoutError):
                    print(f"Error saving frame: {e}")
    
    def start_capture(self):
        """Start the capture process using multiple threads"""
        print("Capture will start in 3 seconds...")
        time.sleep(3)
        
        self.start_time = time.perf_counter()
        
        # Create and start capture thread
        self.capture_thread = Thread(target=self.capture_screen)
        self.capture_thread.start()
        
        # Create and start save thread
        self.save_thread = Thread(target=self.save_frames)
        self.save_thread.start()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Screen Capture')
    parser.add_argument('output_folder', help='Folder to save captures')
    parser.add_argument('--fps', type=int, default=20, help='Frames per second')
    
    args = parser.parse_args()
    
    try:
        import mss
        import cv2
    except ImportError:
        print("Required packages not found. Please install:")
        print("  pip install mss opencv-python")
        return
    
    print("Important: Make sure Terminal/Python has screen recording permissions")
    print("System Settings -> Privacy & Security -> Screen Recording")
    
    capture = ScreenCapture(
        args.output_folder,
        fps=args.fps
    )
    
    print(f"Starting capture... Press Ctrl+C to stop")
    print(f"Saving frames to: {args.output_folder}")
    print(f"Settings: {args.fps} FPS")
    
    try:
        capture.start_capture()

        time.sleep(5)

        capture.stop_capture()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt")
    finally:
        capture.stop_capture()

if __name__ == "__main__":
    main()