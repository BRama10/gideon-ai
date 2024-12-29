import time
from gideon.utils.shared import toBase64
import os

def add_recordings(recordings, logger, source: list[str]):
    """Modified to store base64 images instead of paths"""
    start_time = time.time()
    
    # Get all jpg files in directory
    # image_dir = "/Users/balaji/gideon/temp_photo"
    # source = [name for name in os.listdir(image_dir) if name.lower().endswith('.jpg')]
    logger.info(f"Found {len(source)} JPG files to process")

    with recordings.batch.fixed_size(batch_size=2, concurrent_requests=2) as batch:
        for idx, path in enumerate(source, 1):
            file_start = time.time()
            logger.info(f"Processing file {idx}/{len(source)}: {path}")
            # path = os.path.join(image_dir, name)
            
            # Convert image to base64
            image_base64 = toBase64(path)
            
            batch.add_object({
                "name": path,
                "image_base64": image_base64,  # Store base64 instead of path
                "image": image_base64,  # This is still needed for vectorization
                "mediaType": "image",
                "timestamp": float(path.split('/')[-1].split('_')[1].split('.')[0])  # Extract timestamp from filename
            })
            
            # Delete the file after adding to batch
            os.remove(path)
            
            logger.info(f"File {path} processing took {time.time() - file_start:.2f} seconds")

    if len(recordings.batch.failed_objects) > 0:
        logger.error(f"Failed to import {len(recordings.batch.failed_objects)} objects")
        for failed in recordings.batch.failed_objects:
            logger.error(f"Failed to import object with error: {failed.message}")
    else:
        logger.info("No errors in batch processing")