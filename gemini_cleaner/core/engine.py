"""
Unified Watermark Removal Engine
Combines the best of v1 (rect mask) and v2 (free-draw mask + MoviePy)
into a single, robust processing engine.
"""

import cv2
import numpy as np
from PIL import Image
import tempfile
import os
import time


# ─── Image Processing ────────────────────────────────────────────────

def create_mask_from_rect(image_shape, rect):
    """
    Creates a binary mask from a rectangle.
    rect: (x, y, w, h)
    """
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    x, y, w, h = rect
    # Clamp values to image bounds
    x = max(0, int(x))
    y = max(0, int(y))
    w = min(int(w), image_shape[1] - x)
    h = min(int(h), image_shape[0] - y)
    if w > 0 and h > 0:
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
    return mask


def create_mask_from_rects(image_shape, rects):
    """
    Creates a binary mask from multiple rectangles.
    rects: list of (x, y, w, h)
    """
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    for rect in rects:
        x, y, w, h = rect
        x = max(0, int(x))
        y = max(0, int(y))
        w = min(int(w), image_shape[1] - x)
        h = min(int(h), image_shape[0] - y)
        if w > 0 and h > 0:
            cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
    return mask


def normalize_mask(mask_input):
    """
    Normalize any mask input (PIL Image, numpy array, RGBA, RGB, grayscale)
    into a clean binary uint8 mask.
    """
    if isinstance(mask_input, Image.Image):
        mask_input = np.array(mask_input)

    if len(mask_input.shape) == 3:
        if mask_input.shape[2] == 4:
            # RGBA: use alpha channel
            mask_gray = mask_input[:, :, 3]
        else:
            mask_gray = cv2.cvtColor(mask_input, cv2.COLOR_RGB2GRAY)
    else:
        mask_gray = mask_input

    _, binary_mask = cv2.threshold(mask_gray, 10, 255, cv2.THRESH_BINARY)
    return binary_mask.astype(np.uint8)


def inpaint_image(image, mask, radius=3, method="telea"):
    """
    Inpaints an image using the provided mask.

    Parameters:
        image: PIL Image or numpy array (RGB)
        mask: PIL Image, numpy array, or rect tuple (x,y,w,h)
        radius: inpainting radius (1-20), default 3
        method: 'telea' or 'ns' (Navier-Stokes)

    Returns: PIL Image (processed)
    """
    if isinstance(image, Image.Image):
        img_np = np.array(image)
    else:
        img_np = image.copy()

    # Build mask
    if isinstance(mask, (tuple, list)) and len(mask) == 4 and isinstance(mask[0], (int, float)):
        # Single rect
        binary_mask = create_mask_from_rect(img_np.shape, mask)
    elif isinstance(mask, list) and len(mask) > 0 and isinstance(mask[0], (tuple, list)):
        # Multiple rects
        binary_mask = create_mask_from_rects(img_np.shape, mask)
    else:
        binary_mask = normalize_mask(mask)

    # Resize mask if dimensions don't match
    if binary_mask.shape[:2] != img_np.shape[:2]:
        binary_mask = cv2.resize(binary_mask, (img_np.shape[1], img_np.shape[0]),
                                 interpolation=cv2.INTER_NEAREST)

    # Select algorithm
    flag = cv2.INPAINT_TELEA if method.lower() == "telea" else cv2.INPAINT_NS
    radius = max(1, min(20, int(radius)))

    # Convert RGB to BGR for OpenCV
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # Inpaint
    result_bgr = cv2.inpaint(img_bgr, binary_mask, radius, flag)

    # Convert back to RGB
    result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(result_rgb)


# ─── Video Processing ────────────────────────────────────────────────

def get_first_frame(video_path):
    """
    Extracts the first frame of a video as a PIL Image.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("無法開啟影片檔案")

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise ValueError("影片中沒有可讀取的畫面")

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)


def get_video_info(video_path):
    """
    Returns dict with video metadata: width, height, fps, total_frames, duration.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("無法開啟影片檔案")

    info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
    }
    info["duration"] = info["total_frames"] / info["fps"] if info["fps"] > 0 else 0
    cap.release()
    return info


def process_video(video_path, mask, radius=3, method="telea", progress_callback=None):
    """
    Removes watermark from video frame by frame using OpenCV.

    Parameters:
        video_path: path to input video
        mask: rect tuple, list of rects, or mask image
        radius: inpainting radius
        method: 'telea' or 'ns'
        progress_callback: callable(current_frame, total_frames) for progress updates

    Returns: path to processed video file
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("無法開啟影片檔案")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Create output file
    output_path = tempfile.mktemp(suffix=".mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Build binary mask once
    if isinstance(mask, (tuple, list)) and len(mask) == 4 and isinstance(mask[0], (int, float)):
        binary_mask = create_mask_from_rect((height, width), mask)
    elif isinstance(mask, list) and len(mask) > 0 and isinstance(mask[0], (tuple, list)):
        binary_mask = create_mask_from_rects((height, width), mask)
    else:
        binary_mask = normalize_mask(mask)
        if binary_mask.shape[:2] != (height, width):
            binary_mask = cv2.resize(binary_mask, (width, height),
                                     interpolation=cv2.INTER_NEAREST)

    flag = cv2.INPAINT_TELEA if method.lower() == "telea" else cv2.INPAINT_NS
    radius = max(1, min(20, int(radius)))

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        restored = cv2.inpaint(frame, binary_mask, radius, flag)
        out.write(restored)
        frame_count += 1

        if progress_callback and frame_count % 5 == 0:
            progress_callback(frame_count, total_frames)

    cap.release()
    out.release()

    # Final progress update
    if progress_callback:
        progress_callback(total_frames, total_frames)

    return output_path
