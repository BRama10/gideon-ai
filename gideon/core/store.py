import warnings
import time
import argparse
from datetime import datetime
import logging

from dotenv import load_dotenv
import weaviate, os
from weaviate.classes.config import Property, DataType, Configure, Multi2VecField

def create_weaviate_client(logger):

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

