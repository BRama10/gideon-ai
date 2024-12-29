import time
import os
from threading import Event, Thread
import logging
from datetime import datetime
from typing import Optional
import shutil

from gideon.core.dedup import ImageDeduplicator
from gideon.core.model import LLMMessageBuilder, Message
from gideon.core.store import create_weaviate_client as create_client,  setup_collection

from gideon.analytics.logging import setup_logging

from gideon.mechanisms.record import ScreenCapture
from gideon.mechanisms.retrieve import query_collection
from gideon.mechanisms.save import add_recordings

class GideonCapture:
    def __init__(self, output_folder: str = "./temp_photo", fps: int = 20, dedup_interval: int = 5):
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        
        # Initialize components
        self.output_folder = output_folder
        self.fps = fps
        self.dedup_interval = dedup_interval
        self.stop_event = Event()
        
        # Initialize screen capture
        self.screen_capture = ScreenCapture(output_folder, fps=fps)
        
        # Initialize deduplicator
        self.deduplicator = ImageDeduplicator(threshold=10)
        
        # Initialize vector DB
        self.vector_client = create_client(self._setup_logging())
        self.recordings = setup_collection(self.vector_client, self._setup_logging())
        
        # Initialize LLM interface
        self.llm_builder = LLMMessageBuilder()
        
        # Background thread for deduplication and vector DB updates
        self.dedup_thread: Optional[Thread] = None
        
    def _setup_logging(self):
        """Setup logging configuration."""
        logger = logging.getLogger('gideon')
        logger.setLevel(logging.INFO)
        
        # Create file handler with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        handler = logging.FileHandler(f'gideon_{timestamp}.log')
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        return logger

    def _dedup_and_update_db(self):
        """Background process for deduplication and vector DB updates."""
        logger = self._setup_logging()
        
        while not self.stop_event.is_set():
            try:
                # Wait for the specified interval
                time.sleep(self.dedup_interval)
                
                # Run deduplication
                logger.info("Starting deduplication process...")
                representatives, _ = self.deduplicator.deduplicate(self.output_folder, method='highest_res')
                
                if representatives:
                    # logger.info(f"Found {len(representatives)} unique images")
                    
                    # Update vector DB with deduplicated images
                    logger.info("Updating vector database...")
                    add_recordings(self.recordings, logger, list(representatives))
                    
                    # Clean up processed images (SKIP FOR NOW)
                    logger.info("Cleaning up processed images...")
                    for file in os.listdir(self.output_folder):
                        file_path = os.path.join(self.output_folder, file)
                        if os.path.isfile(file_path) and file.endswith('.jpg'):
                            os.remove(file_path)
                    
                logger.info("Deduplication cycle completed")
                
            except Exception as e:
                logger.error(f"Error in deduplication process: {str(e)}")
                continue

    def start(self):
        """Start all background processes."""
        # Start screen recording
        self.screen_capture.start_capture()
        
        # Start deduplication and DB update thread
        self.dedup_thread = Thread(target=self._dedup_and_update_db)
        self.dedup_thread.start()
        
        print("Gideon capture system started")
        print(f"Recording to: {self.output_folder}")
        print(f"FPS: {self.fps}")
        print(f"Deduplication interval: {self.dedup_interval} seconds")

    def stop(self):
        """Stop all processes cleanly."""
        print("\nStopping Gideon capture system...")
        
        # Stop screen recording
        self.screen_capture.stop_capture()
        
        # Stop deduplication thread
        self.stop_event.set()
        if self.dedup_thread and self.dedup_thread.is_alive():
            self.dedup_thread.join()
        
        # Close vector DB client
        if hasattr(self, 'vector_client'):
            self.vector_client.close()
        
        # Clean up output directory
        if os.path.exists(self.output_folder):
            shutil.rmtree(self.output_folder)
        
        print("Gideon capture system stopped")

    def query(self, question: str) -> str:
        """Query the system about screen recording content."""
        try:
            # Create a new message with the question
            message = self.llm_builder.create_message("user")
            message.add_text(question)
            
            # Get relevant images from vector DB
            response = self.recordings.query.near_text(
                query=question,
                return_properties=['image_base64', 'timestamp'],  # Get base64 data instead of path
                limit=3
            )
            
            # Add relevant images to the message using base64 data
            for obj in response.objects:
                # The base64 data can be directly used in the message
                message.add_image_base64(obj.properties['image_base64'])
                print(f"Adding image from timestamp: {obj.properties['timestamp']}")
            
            # Get response from LLM
            answer = self.llm_builder.send(max_tokens=500)
            return answer
            
        except Exception as e:
            return f"Error processing query: {str(e)}"
