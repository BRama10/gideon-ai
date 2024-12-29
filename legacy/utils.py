import json
import base64
import requests
from PIL import Image
import os
import subprocess
import platform

# Helper function to convert a file to base64 representation
def toBase64(path):
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

def json_print(data):
    """Pretty print JSON data with proper indentation."""
    print(json.dumps(data, indent=2))

def display_media(item):
    """
    Display image or video files using the default system viewer.
    
    Args:
        item (dict): Dictionary containing 'path' and 'mediaType' keys
    """
    path = item["path"]
    
    if not os.path.exists(path):
        print(f"Error: File not found at {path}")
        return
    
    # Get the operating system
    system = platform.system()
    
    if item["mediaType"] == "image":
        # For images, we can use PIL to show them
        try:
            img = Image.open(path)
            img.show()
        except Exception as e:
            print(f"Error displaying image: {e}")
            
            # Fallback to system viewer if PIL fails
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
    
    elif item["mediaType"] == "video":
        # Use system default video player
        try:
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
        except Exception as e:
            print(f"Error playing video: {e}")

def url_to_base64(url):
    """
    Convert an online image to base64 representation.
    
    Args:
        url (str): URL of the image
    
    Returns:
        str: Base64 encoded string of the image
    """
    try:
        image_response = requests.get(url)
        image_response.raise_for_status()  # Raise an exception for bad status codes
        content = image_response.content
        return base64.b64encode(content).decode('utf-8')
    except Exception as e:
        print(f"Error converting URL to base64: {e}")
        return None

def file_to_base64(path):
    """
    Convert a local file to base64 representation.
    
    Args:
        path (str): Path to the local file
    
    Returns:
        str: Base64 encoded string of the file
    """
    try:
        with open(path, 'rb') as file:
            return base64.b64encode(file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error converting file to base64: {e}")
        return None
