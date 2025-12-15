import rawpy
import numpy as np
import cv2
import io
from typing import Union, Optional

def load_raw_image(file_obj: Union[str, io.BytesIO]) -> Optional[np.ndarray]:
    """
    Load a RAW image and return it as a linear 16-bit RGB numpy array.
    
    Args:
        file_obj: File path or file-like object containing RAW data.
        
    Returns:
        np.ndarray: Linear RGB image (uint16) or None if failed.
    """
    try:
        with rawpy.imread(file_obj) as raw:
            # postprocess to get linear RGB
            # gamma=(1,1) -> Linear (no gamma correction)
            # no_auto_bright=True -> Do not automatically adjust brightness
            # output_bps=16 -> 16-bit depth for higher dynamic range
            # postprocess to get Linear 16-bit RGB (gamma=1,1)
            # This provides the physical light data needed for the Linear Optical Pipeline
            rgb = raw.postprocess(
                gamma=(1, 1),
                no_auto_bright=True,
                use_camera_wb=True, 
                bright=1.0, # Default scale, can be adjusted or auto-exposure handled in renderer
                output_bps=16
            )
            return rgb
    except Exception as e:
        print(f"Error loading RAW image: {e}")
        return None

def normalize_16bit_to_8bit(image_16: np.ndarray) -> np.ndarray:
    """Safely convert 16-bit image to 8-bit for display/processing if needed."""
    return (image_16 // 256).astype(np.uint8)

def ensure_uint8(image: np.ndarray) -> np.ndarray:
    """Ensure image is uint8 BGR (standard OpenCV format) for the current pipeline."""
    if image.dtype == np.uint16:
        # Simple scaling for now. In a full linear pipeline we might keep 16-bit longer.
        # But Phos 0.1.1 logic mostly assumes 0-255 inputs implicitly in some places or floats.
        # renderer._calculate_luminance converts to float 0-1 anyway.
        # So we can pass 8-bit or refactor renderer to handle 16-bit.
        # For now, let's keep compatibility by converting to 8-bit, 
        # BUT since we want the 'Raw Benefit' (High Dynamic Range), 
        # we should ideally feed the high dynamic range float to the renderer.
        
        # Current renderer:
        # b = b.astype(np.float32) / 255.0
        # It assumes 8-bit input.
        
        # Let's convert to 8-bit for now to match interface, 
        # but a better approach later is to update renderer to accept 16-bit or float.
        return (image / 256).astype(np.uint8)
        
    return image.astype(np.uint8)
