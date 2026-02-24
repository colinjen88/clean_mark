# 使用輕量級 Python 映像檔
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴 (OpenCV 需要一些系統庫)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 複製需求文件並安裝依賴
COPY gemini_cleaner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案原始碼
COPY gemini_cleaner/ ./gemini_cleaner/

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 暴露 Streamlit 預設連接埠
EXPOSE 8501

# 啟動命令
WORKDIR /app/gemini_cleaner
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
