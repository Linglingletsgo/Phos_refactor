import cv2
import numpy as np
import sys
import os

# Add current dir to path to find phos module
sys.path.append(os.getcwd())

from phos.core import FilmRenderer
from phos.config import get_preset

def test_pipeline():
    print("Testing FilmRenderer Pipeline...")
    
    # Create a dummy linear float image (HDR)
    # 500x500 image, with a super bright spot in the middle
    img = np.zeros((500, 500, 3), dtype=np.float32)
    cv2.circle(img, (250, 250), 20, (50.0, 50.0, 50.0), -1) # Bright spot
    
    preset = get_preset("Kodak Portra 400")
    # Test with one of the new presets to ensure defaults work
    renderer = FilmRenderer(preset=preset) 
    
    print("running process with PORTRA_400...")
    result = renderer.process(img, iso=400, tone_style="filmic")
    
    print(f"Output shape: {result.shape}")
    print(f"Output dtype: {result.dtype}")
    
    if result.shape == (500, 500, 3) and result.dtype == np.uint8:
        print("SUCCESS: Pipeline run finished with correct output format.")
    else:
        print("FAILURE: Output format mismatch.")

if __name__ == "__main__":
    test_pipeline()
