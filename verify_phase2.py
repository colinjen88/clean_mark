try:
    import gradio as gr
    import cv2
    import numpy
    import moviepy as mp
    from PIL import Image
    print("All Phase 2 imports successful!")
except ImportError as e:
    print(f"Import failed: {e}")
    exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    exit(1)
