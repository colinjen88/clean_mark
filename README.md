# CleanMark Pro ✨

CleanMark Pro 是一套功能強大的影像與影片浮水印移除工具，內建現代化的深色模式 UI (基於 Streamlit)。

## 專案結構重整 (v3 模組化架構)
目前專案已整合為單一 Git 儲存庫 (Mono-repo)。

- `gemini_cleaner/`: 核心應用程式目錄
  - `app.py`: 應用的進入點 (Entry-point)，負責路由與全域配置
  - `views/`: 獨立的頁面模組 (首頁、單圖、批次、影片)
  - `utils/`: 共用的 UI 元件與輔助函式庫
  - `core/`: 影像處理核心演算法 (OpenCV Inpainting 等)

## 啟動方式
請確保您已安裝所有依賴項目 (參考 `gemini_cleaner/requirements.txt`)，建議在虛擬環境(`.venv`)下執行：

```bash
cd gemini_cleaner
python -m streamlit run app.py
```
