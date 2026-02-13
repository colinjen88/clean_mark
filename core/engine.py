import cv2
import numpy as np
from PIL import Image
import tempfile
import os
from moviepy import VideoFileClip, ImageSequenceClip

def inpaint_image(image, mask_image):
    """
    Inpaints an image using the provided mask.
    image: PIL Image or numpy array (RGB)
    mask_image: PIL Image or numpy array (Binary Mask)
    """
    if isinstance(image, Image.Image):
        image = np.array(image)
    
    if isinstance(mask_image, Image.Image):
        mask_image = np.array(mask_image)
        
    # Handle RGBA or Multichannel masks
    if len(mask_image.shape) == 3:
        if mask_image.shape[2] == 4:
            # Use Alpha channel if it's an RGBA layer from Gradio
            # Often, the drawing is in the RGB channels and the rest is transparent (Alpha=0)
            # We want to inpaint where alpha > 0 (or where any color is present)
            # Let's use the alpha channel as the base mask
            mask_image = mask_image[:, :, 3]
        else:
            mask_image = cv2.cvtColor(mask_image, cv2.COLOR_RGB2GRAY)
    
    # Threshold mask to ensure binary (any non-black pixel becomes white)
    _, mask_image = cv2.threshold(mask_image, 10, 255, cv2.THRESH_BINARY)
    
    # Convert RGB to BGR for OpenCV
    img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    # Inpaint
    # simple fast method: INPAINT_TELEA
    result_bgr = cv2.inpaint(img_bgr, mask_image, 3, cv2.INPAINT_TELEA)
    
    # Convert back to RGB
    result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
    
    return Image.fromarray(result_rgb)

def process_video_frames(video_path, mask_image, start_time=0, end_time=None):
    """
    Processes a video file, applying the mask to every frame.
    Uses MoviePy for easier audio handling and frame iteration.
    """
    clip = VideoFileClip(video_path)
    
    if end_time is None:
        end_time = clip.duration
        
    # Ensure mask is prepared once
    if isinstance(mask_image, Image.Image):
        mask_image = np.array(mask_image)
    if len(mask_image.shape) == 3:
        if mask_image.shape[2] == 4:
            mask_binary = mask_image[:, :, 3]
        else:
            mask_binary = cv2.cvtColor(mask_image, cv2.COLOR_RGB2GRAY)
    else:
        mask_binary = mask_image
        
    _, mask_binary = cv2.threshold(mask_binary, 10, 255, cv2.THRESH_BINARY)
    
    # Function to transform each frame
    def process_frame(frame):
        # Frame is HxWx3 numpy array (RGB)
        # Convert to BGR
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Resize mask if needed (though UI should enforce matching size)
        current_mask = mask_binary
        if frame.shape[:2] != current_mask.shape[:2]:
            current_mask = cv2.resize(mask_binary, (frame.shape[1], frame.shape[0]))
            
        # Inpaint
        restored_bgr = cv2.inpaint(frame_bgr, current_mask, 3, cv2.INPAINT_TELEA)
        
        # Back to RGB
        return cv2.cvtColor(restored_bgr, cv2.COLOR_BGR2RGB)
    
    # Apply processing
    # We only process the subclip if specific times are given, or whole clip
    # subclip = clip.subclip(start_time, end_time) 
    # For now, let's process the whole clip for simplicity in V2 MVP
    
    new_clip = clip.image_transform(process_frame)
    
    # Write output
    output_path = tempfile.mktemp(suffix=".mp4")
    new_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
    
    return output_path
