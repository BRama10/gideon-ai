import time
from gideon.utils.shared import json_print, display_media

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
