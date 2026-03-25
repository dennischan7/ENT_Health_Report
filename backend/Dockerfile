FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies and Chinese fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    fonts-wqy-zenhei \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Clear matplotlib font cache (will be rebuilt with new fonts)
RUN rm -rf /root/.cache/matplotlib

# Install Python dependencies with Chinese mirror
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]