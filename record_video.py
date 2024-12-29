import time
import os
from datetime import datetime, timedelta
import subprocess
from threading import Event
import signal

class ScreenRecorder:
    def __init__(self, output_folder, chunk_duration=5, fps=30):
        self.output_folder = output_folder
        self.chunk_duration = chunk_duration
        self.fps = fps
        self.stop_event = Event()
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        print("\nStopping recording...")
        self.stop_event.set()
    
    def record_chunk(self, start_time):
        """Record a single chunk using ffmpeg screen capture"""
        end_time = start_time + timedelta(seconds=self.chunk_duration)
        filename = f"{start_time.strftime('%Y-%m-%d_%H-%M-%S')};;{end_time.strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
        filepath = os.path.join(self.output_folder, filename)
        
        command = [
            'ffmpeg',
            '-f', 'avfoundation',  # macOS screen capture
            '-capture_cursor', '1',  # Capture cursor
            '-i', "1:none",  # Capture main screen, no audio
            '-t', str(self.chunk_duration),  # Duration
            '-r', str(self.fps),  # Frame rate
            '-preset', 'ultrafast',
            '-c:v', 'h264',
            '-crf', '22',  # Good quality
            '-pix_fmt', 'yuv420p',
            filepath
        ]
        
        try:
            process = subprocess.run(command, 
                                   capture_output=True,
                                   timeout=self.chunk_duration + 2)  # Allow 2s buffer
            if process.returncode == 0:
                print(f"Completed chunk: {filename}")
            else:
                print(f"Error recording chunk: {process.stderr.decode()}")
        except subprocess.TimeoutExpired:
            print(f"Chunk timed out: {filename}")
    
    def start_recording(self):
        """Start the recording process"""
        print("Recording will start in 3 seconds...")
        time.sleep(3)  # Give time to switch windows if needed
        
        try:
            while not self.stop_event.is_set():
                chunk_start_time = datetime.now()
                self.record_chunk(chunk_start_time)
        finally:
            print("Recording stopped")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Screen Recorder')
    parser.add_argument('output_folder', help='Folder to save recordings')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    parser.add_argument('--chunk-duration', type=int, default=5, 
                        help='Duration of each video chunk in seconds')
    
    args = parser.parse_args()
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is not installed or not found in PATH")
        print("Please install ffmpeg:")
        print("  macOS: brew install ffmpeg")
        return
    
    # Make sure screen capture permissions are granted
    print("Important: Make sure Terminal/Python has screen recording permissions")
    print("System Settings -> Privacy & Security -> Screen Recording")
    
    recorder = ScreenRecorder(
        args.output_folder,
        chunk_duration=args.chunk_duration,
        fps=args.fps
    )
    
    print(f"Starting recording... Press Ctrl+C to stop")
    print(f"Saving chunks to: {args.output_folder}")
    print(f"Settings: {args.fps} FPS, {args.chunk_duration}s chunks")
    
    recorder.start_recording()

if __name__ == "__main__":
    main()