from PIL import Image
import numpy as np
from pathlib import Path
from collections import defaultdict
import random
from typing import Dict, List, Tuple, Set
import os

class ImageDeduplicator:
    def __init__(self, threshold: int = 10):
        """
        Initialize the deduplicator with a similarity threshold.
        
        Args:
            threshold (int): Maximum hamming distance to consider images similar (default: 10)
        """
        self.threshold = threshold
        self.image_hashes = {}  # Store image hashes
        self.groups = defaultdict(list)  # Store image groups
        self.representatives = set()  # Store representative images
        
    def calculate_dhash(self, image_path: str, hash_size: int = 8) -> str:
        """Calculate difference hash for an image."""
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale and resize
                img = img.convert('L').resize((hash_size + 1, hash_size))
                pixels = np.array(img)
                diff = pixels[:, 1:] > pixels[:, :-1]
                return ''.join(str(int(d)) for d in diff.flatten())
        except Exception as e:
            print(f"Error processing {image_path}: {str(e)}")
            return None

    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate hamming distance between two hashes."""
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    def get_image_resolution(self, image_path: str) -> int:
        """Get total pixels in image."""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                return width * height
        except Exception:
            return 0

    def process_directory(self, directory_path: str) -> None:
        """
        Process all images in a directory and calculate their hashes.
        
        Args:
            directory_path (str): Path to directory containing images
        """
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        self.image_hashes.clear()
        
        for path in Path(directory_path).rglob('*'):
            if path.suffix.lower() in valid_extensions:
                hash_value = self.calculate_dhash(str(path))
                if hash_value:
                    self.image_hashes[str(path)] = hash_value

    def group_similar_images(self) -> None:
        """Group similar images based on hash similarity."""
        self.groups.clear()
        processed = set()
        
        for path1, hash1 in self.image_hashes.items():
            if path1 in processed:
                continue
                
            current_group = []
            for path2, hash2 in self.image_hashes.items():
                if path2 not in processed and self.hamming_distance(hash1, hash2) <= self.threshold:
                    current_group.append(path2)
                    processed.add(path2)
                    
            if current_group:
                group_id = len(self.groups)
                self.groups[group_id] = current_group

    def select_representatives(self, method: str = 'first') -> Set[str]:
        """
        Select representative images from each group.
        
        Args:
            method (str): Method to select representative ('first', 'random', or 'highest_res')
        
        Returns:
            Set of paths to representative images
        """
        self.representatives.clear()
        
        for group in self.groups.values():
            if method == 'random':
                representative = random.choice(group)
            elif method == 'highest_res':
                representative = max(group, key=self.get_image_resolution)
            else:  # 'first'
                representative = group[0]
                
            self.representatives.add(representative)
            
        return self.representatives

    def get_group_statistics(self) -> Dict:
        """
        Get statistics about image groups.
        
        Returns:
            Dictionary containing group statistics
        """
        stats = {
            'total_images': len(self.image_hashes),
            'unique_groups': len(self.groups),
            'total_duplicates': len(self.image_hashes) - len(self.representatives),
            'group_sizes': [len(group) for group in self.groups.values()],
            'largest_group_size': max(len(group) for group in self.groups.values()) if self.groups else 0,
            'average_group_size': sum(len(group) for group in self.groups.values()) / len(self.groups) if self.groups else 0
        }
        
        # Add group size distribution
        size_distribution = defaultdict(int)
        for group in self.groups.values():
            size_distribution[len(group)] += 1
        stats['size_distribution'] = dict(size_distribution)
        
        return stats

    def get_group_members(self, representative: str) -> List[str]:
        """
        Get all images that were grouped with a representative image.
        
        Args:
            representative (str): Path to representative image
            
        Returns:
            List of paths to similar images
        """
        for group in self.groups.values():
            if representative in group:
                return [path for path in group if path != representative]
        return []

    def deduplicate(self, directory_path: str, method: str = 'first') -> Tuple[Set[str], Dict]:
        """
        Main method to perform deduplication.
        
        Args:
            directory_path (str): Path to directory containing images
            method (str): Method to select representatives
            
        Returns:
            Tuple of (representative image paths, statistics)
        """
        self.process_directory(directory_path)
        self.group_similar_images()
        representatives = self.select_representatives(method)
        statistics = self.get_group_statistics()
        return representatives, statistics

# Example usage:
if __name__ == "__main__":
    # Initialize deduplicator
    dedup = ImageDeduplicator(threshold=10)
    
    # Process directory
    image_dir = "/Users/balaji/gideon/temp_photo"
    representatives, stats = dedup.deduplicate(image_dir, method='highest_res')
    
    # Print results
    print(f"\nFound {len(representatives)} unique images out of {stats['total_images']} total images")
    print(f"Representatives", representatives)
    print(f"Removed {stats['total_duplicates']} duplicate images")
    print("\nGroup size distribution:")
    for size, count in stats['size_distribution'].items():
        print(f"Groups of size {size}: {count}")
        
    # Print complete groups without truncation
    for rep in representatives:
        similar_images = dedup.get_group_members(rep)
        print(f"\nRepresentative: {rep}")
        print(f"Similar images: {len(similar_images)}")
        for img in similar_images:  # Show all similar images
            print(f"  - {img}")