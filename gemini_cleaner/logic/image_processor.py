import cv2
import numpy as np
from PIL import Image

def create_mask_from_rect(image_shape, rect):
    """
    Creates a binary mask from a rectangle.
    rect: (x, y, w, h)
    """
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    x, y, w, h = rect
    cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
    return mask

def remove_watermark_image(image, rect):
    """
    Removes watermark from an image using the specified rectangle.
    image: PIL Image
    rect: (x, y, w, h) tuple
    Returns: PIL Image (processed)
    """
    # Convert PIL to OpenCV format (RGB -> BGR)
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Create mask
    mask = create_mask_from_rect(img_cv.shape, rect)
    
    # Inpaint
    # 3 is the radius of a circular neighborhood of each point inpainting
    restored = cv2.inpaint(img_cv, mask, 3, cv2.INPAINT_TELEA)
    
    # Convert back to PIL (BGR -> RGB)
    result_image = Image.fromarray(cv2.cvtColor(restored, cv2.COLOR_BGR2RGB))
    return result_image
