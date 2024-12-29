import warnings
import time
import argparse
from datetime import datetime
import logging

from dotenv import load_dotenv
import weaviate, os
from weaviate.classes.config import Property, DataType, Configure, Multi2VecField
from dedup import ImageDeduplicator
from utils import toBase64, url_to_base64, json_print, display_media, file_to_base64

warnings.filterwarnings('ignore')

def setup_logging():
    # Create a logger
    logger = logging.getLogger('weaviate_operations')
    logger.setLevel(logging.INFO)
    
    # Create file handler with timestamp in filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    fh = logging.FileHandler(f'weaviate_execution_{timestamp}.log')
    fh.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(fh)
    
    return logger

def create_client(logger):
    start_time = time.time()
    try:
        load_dotenv()
        vertex_key = os.getenv("VERTEX_APIKEY")

        client = weaviate.connect_to_embedded(
            version="1.28.2",
            environment_variables={
                "ENABLE_MODULES": "multi2vec-google",
                "LOG_LEVEL":"fatal"
            },
            headers={
                "X-Goog-Vertex-Api-Key": vertex_key,
            },
            persistence_data_path='./vectordb/'
        )
        
        logger.info(f"Client creation took {time.time() - start_time:.2f} seconds")
        logger.info(f"Client Is Ready: {client.is_ready()}")
        return client
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        raise

def setup_collection(client, logger):
    start_time = time.time()
    
    if(client.collections.exists("Recordings")):
        logger.info("Deleting existing Recordings collection")
        delete_start = time.time()
        client.collections.delete("Recordings")
        logger.info(f"Collection deletion took {time.time() - delete_start:.2f} seconds")

    logger.info("Creating new Recordings collection")
    create_start = time.time()
    client.collections.create(
        name="Recordings",
        vectorizer_config=Configure.Vectorizer.multi2vec_palm(
            image_fields=["image"],
            video_fields=["video"],
            project_id="spiritual-vent-433203-b2",
            location="us-east1",
            model_id="multimodalembedding@001",
            dimensions=1408,
        )
    )
    logger.info(f"Collection creation took {time.time() - create_start:.2f} seconds")
    
    recordings = client.collections.get("Recordings")
    logger.info(f"Total collection setup took {time.time() - start_time:.2f} seconds")
    return recordings

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

def query_collection(client, logger):
    start_time = time.time()
    
    recordings = client.collections.get("Recordings")
    
    # Aggregate
    agg_start = time.time()
    agg = recordings.aggregate.over_all(group_by="mediaType")
    logger.info(f"Aggregation took {time.time() - agg_start:.2f} seconds")
    
    for group in agg.groups:
        logger.info(f"Aggregate group: {group}")

    # Query
    query_start = time.time()
    response = recordings.query.near_text(
        query="jupyter notebook",
        return_properties=['name','path','mediaType'],
        limit=2
    )
    logger.info(f"Query execution took {time.time() - query_start:.2f} seconds")

    for obj in response.objects:
        json_print(obj.properties)
        display_media(obj.properties)

    logger.info(f"Total query operations took {time.time() - start_time:.2f} seconds")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Weaviate image processing script')
    parser.add_argument('--query-only', action='store_true', 
                      help='Skip collection creation and data insertion, only perform queries')
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging()
    total_start_time = time.time()

    client = None
    try:
        logger.info("Starting Weaviate operations")
        client = create_client(logger)

        if not args.query_only:
            logger.info("Starting full process including collection setup and data insertion")
            recordings = setup_collection(client, logger)
            add_recordings(recordings, logger)
        else:
            logger.info("Skipping collection setup and data insertion, proceeding to queries")

        query_collection(client, logger)

    except Exception as e:
        logger.error(f'Exception Occurred: {str(e)}')
    finally:
        if client:
            client.close()
            logger.info("Client connection closed")
        
        logger.info(f"Total execution time: {time.time() - total_start_time:.2f} seconds")

if __name__ == "__main__":
    main() 