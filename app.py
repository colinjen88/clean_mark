import gradio as gr
import os
import sys
import numpy as np
from PIL import Image
import tempfile
import cv2
import zipfile
import shutil

# Add core logic to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
try:
    from engine import inpaint_image, process_video_frames
except ImportError:
    # Fallback for when running directly or path issues
    import engine
    inpaint_image = engine.inpaint_image
    process_video_frames = engine.process_video_frames

def process_img(input_dict):
    """
    Handler for Image Inpainting tab.
    input_dict: dictionary from gr.ImageEditor containing 'background' and 'layers' (paths)
    """
    if input_dict is None:
        return None
        
    bg_path = input_dict.get("background")
    layers = input_dict.get("layers", [])
    mask_path = layers[0] if layers else None
    
    if bg_path is None:
        return None
        
    image = Image.open(bg_path).convert("RGB")
    
    # If no mask drawn, return original
    if mask_path is None:
        return image
        
    # Open mask
    mask = Image.open(mask_path)
        
    # Process
    try:
        result = inpaint_image(image, mask)
        return result
    except Exception as e:
        print(f"Error processing image: {e}")
        return image

def extract_first_frame(video_path):
    if video_path is None:
        return None
    
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Since ImageEditor type='filepath', we must return a path
        img = Image.fromarray(frame_rgb)
        temp_path = tempfile.mktemp(suffix=".png")
        img.save(temp_path)
        return temp_path
    return None

def process_vid(video_path, mask_dict):
    """
    Handler for Video Inpainting tab.
    """
    if video_path is None or mask_dict is None:
        return None
        
    layers = mask_dict.get("layers", [])
    mask_path = layers[0] if layers else None
    if mask_path is None:
        return video_path
        
    try:
        gr.Info("正在讀取遮罩與影片...")
        mask = Image.open(mask_path)
        gr.Info("開始影片修復，這可能需要幾分鐘...")
        output_path = process_video_frames(video_path, mask)
        gr.Info("影片修復完成！")
        return output_path
    except Exception as e:
        raise gr.Error(f"影片處理失敗：{e}")

def process_batch(ref_dict, files):
    """
    Handler for Batch Processing tab.
    ref_dict: ImageEditor output (used for mask)
    files: List of file paths
    """
    if ref_dict is None or files is None or len(files) == 0:
        return None
        
    layers = ref_dict.get("layers", [])
    mask_path = layers[0] if layers else None
    if mask_path is None:
        raise gr.Error("請先在參考圖上繪製浮水印遮罩")
    
    # Load mask
    try:
        mask = Image.open(mask_path)
    except Exception as e:
        raise gr.Error(f"無法讀取遮罩：{e}")
        
    # Create a temp directory for outputs
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(tempfile.gettempdir(), "cleaned_batch.zip")
    
    processed_count = 0
    
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in files:
                try:
                    # Open image
                    img = Image.open(file_path).convert("RGB")
                    
                    # Process
                    # Note: engine expects PIL image or Numpy
                    result = inpaint_image(img, mask)
                    
                    # Save to temp
                    base_name = os.path.basename(file_path)
                    save_path = os.path.join(temp_dir, f"cleaned_{base_name}")
                    result.save(save_path)
                    
                    # Add to zip
                    zipf.write(save_path, arcname=f"cleaned_{base_name}")
                    processed_count += 1
                except Exception as e:
                    print(f"Skipping file {file_path}: {e}")
                    
    except Exception as e:
        raise gr.Error(f"Batch processing failed: {e}")
    finally:
        # Cleanup temp dir
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    if processed_count == 0:
        raise gr.Error("處理失敗，未生成任何圖片")
        
    return zip_path

# Build UI
with gr.Blocks(title="Gemini 浮水印去除工具 (Phase 2)", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 Gemini 浮水印去除工具 (專業版)")
    gr.Markdown("使用先進的 AI 修復技術，輕鬆去除圖片與影片中的浮水印。")
    
    with gr.Tab("🖼️ 智能圖片修復"):
        with gr.Row():
            with gr.Column():
                img_input = gr.ImageEditor(
                    label="上傳圖片並塗抹浮水印",
                    type="filepath",
                    brush=gr.Brush(colors=["#FF0000"], color_mode="fixed"),
                    interactive=True
                )
                img_btn = gr.Button("開始修復", variant="primary")
            
            with gr.Column():
                img_output = gr.Image(label="修復結果")
                
        img_btn.click(process_img, inputs=img_input, outputs=img_output)
    
    with gr.Tab("📦 批量處理工廠"):
        gr.Markdown("### 1. 定義浮水印位置")
        ref_input = gr.ImageEditor(
            label="上傳一張參考圖並塗抹浮水印 (此遮罩將應用於所有圖片)",
            type="filepath",
            brush=gr.Brush(colors=["#FF0000"], color_mode="fixed"),
            interactive=True,
            height=400
        )
        
        gr.Markdown("### 2. 上傳批量圖片")
        batch_files = gr.File(
            label="選擇多張圖片", 
            file_count="multiple",
            file_types=["image"]
        )
        
        batch_btn = gr.Button("開始批量處理", variant="primary")
        batch_output = gr.File(label="下載處理結果 (ZIP)")
        
        batch_btn.click(
            process_batch,
            inputs=[ref_input, batch_files],
            outputs=batch_output
        )

    with gr.Tab("🎬 影片去除 (時間軸修復)"):
        with gr.Row():
            with gr.Column():
                vid_input = gr.Video(label="上傳影片")
                # We need an ImageEditor to draw the mask on the first frame
                # Steps: 1. Upload Video -> 2. Extract Frame -> 3. Draw Mask -> 4. Process
                
                extract_btn = gr.Button("截取第一幀以繪製遮罩", size="sm")
                
                mask_input = gr.ImageEditor(
                    label="在預覽圖上塗抹浮水印區域",
                    type="filepath",
                    brush=gr.Brush(colors=["#FF0000"], color_mode="fixed"),
                    interactive=True,
                    visible=True # Always visible? Or show after click? Let's keep visible for UX.
                )
                
                vid_process_btn = gr.Button("開始影片修復", variant="primary")
                
            with gr.Column():
                vid_output = gr.Video(label="修復後的影片")
        
        # Interactions
        vid_input.change(extract_first_frame, inputs=vid_input, outputs=mask_input)
        # Also allow manual click
        extract_btn.click(extract_first_frame, inputs=vid_input, outputs=mask_input)
        
        vid_process_btn.click(
            process_vid, 
            inputs=[vid_input, mask_input], 
            outputs=vid_output
        )

if __name__ == "__main__":
    demo.launch(inbrowser=True)
