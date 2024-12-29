import logging
import datetime

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