# Gemini 浮水印去除工具 (Gemini Watermark Cleaner)

這是一個本地開發的強大工具，專門用於去除 Google Gemini Pro 生成內容中的浮水印。

## 功能特點 (Features)

1.  **圖片去浮水印 (Image Watermark Removal)**
    - 支持 JPG, PNG, WEBP 等格式。
    - 直觀的畫布操作：直接在圖片上框選浮水印區域。
    - 智能修復算法 (Inpainting) 自動填補缺失像素。

2.  **批量圖片處理 (Batch Image Processing)**
    - 一次上傳多張圖片。
    - 統一設定浮水印位置，自動批量處理。
    - 結果自動打包為 ZIP 下載。

3.  **影片去浮水印 (Video Watermark Removal)**
    - 支持 MP4, MOV, AVI 等格式。
    - 自動截取影片第一幀作為預覽。
    - 在預覽圖上框選浮水印，系統自動逐幀修復。

## 安裝與執行 (Installation & Usage)

1.  確保已安裝 Python 3.8+。
2.  安裝依賴套件：
    ```bash
    pip install -r requirements.txt
    ```
3.  啟動應用程式：
    ```bash
    streamlit run app.py
    ```
4.  瀏覽器將自動開啟操作界面。

## 技術棧
- **UI**: Streamlit
- **圖像處理**: OpenCV, Pillow, Numpy
- **交互組件**: streamlit-drawable-canvas

## 注意事項
- 本工具僅用於去除視覺浮水印，無法移除隱形的 SynthID。
- 請合理使用，尊重版權。
