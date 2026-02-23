try:
    import cv2
    import streamlit
    import numpy
    from PIL import Image
    from streamlit_drawable_canvas import st_canvas
    print("All imports successful!")
except ImportError as e:
    print(f"Import failed: {e}")
    exit(1)
