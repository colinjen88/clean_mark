import cv2
import numpy as np
import tempfile
import os
from PIL import Image

def get_first_frame(video_path):
    """
    Extracts the first frame of a video as a PIL Image.
    video_path: Path to input video file
    Returns: PIL Image
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("無法讀取影片")
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise ValueError("影片中沒有畫面")
        
    # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)

def remove_watermark_video(video_path, rect):
    """
    Removes watermark from a video using the specified rectangle.
    video_path: Path to input video file
    rect: (x, y, w, h) tuple
    Returns: Path to processed video file
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError("Error opening video file")

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Create temp output file
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    output_path = temp_output.name
    temp_output.close()
    
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Be careful with codecs, 'mp4v' is generally safe
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Create mask once
    mask = np.zeros((height, width), dtype=np.uint8)
    x, y, w, h = rect
    cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Inpaint frame
        restored_frame = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
        
        # Write frame
        out.write(restored_frame)
        frame_count += 1
        
    cap.release()
    out.release()
    
    return output_path
