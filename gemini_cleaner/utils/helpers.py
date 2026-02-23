def get_canvas_dimensions(img_width, img_height, max_width=600):
    """Calculate responsive canvas dimensions that fit the container."""
    canvas_width = min(img_width, max_width)
    ratio = canvas_width / img_width
    canvas_height = int(img_height * ratio)
    return canvas_width, canvas_height, ratio


def extract_rects_from_canvas(canvas_result, ratio):
    """Extract rectangle coordinates from canvas result, scaled to original image size."""
    rects = []
    if canvas_result.json_data is not None:
        for obj in canvas_result.json_data.get("objects", []):
            if obj.get("type") == "rect":
                rects.append((
                    int(obj["left"] / ratio),
                    int(obj["top"] / ratio),
                    int(obj["width"] / ratio),
                    int(obj["height"] / ratio)
                ))
    return rects


def format_duration(seconds):
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds:.1f} 秒"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes} 分 {secs:.0f} 秒"
