# ==========================================
# 第一阶段：构建依赖层 (Builder)
# ==========================================
# 降级到 python:3.11-slim 以获得最佳兼容性
FROM python:3.11-slim as builder

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 替换 apt 源为阿里云 (Debian Bookworm)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装依赖到指定目录
# 增加 --upgrade pip 以防 pip 版本过老不支持某些 wheel
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --target=/install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# ==========================================
# 第二阶段：运行层 (Runtime)
# ==========================================
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1
ENV IMAGEIO_FFMPEG_EXE=/usr/bin/ffmpeg

# 安装运行时的系统依赖 (FFmpeg)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制安装好的库 (注意路径对应 python3.11)
COPY --from=builder /install /usr/local/lib/python3.11/site-packages
# 如果有 bin 文件也需要复制 (如 uvicorn)
COPY --from=builder /install/bin /usr/local/bin

COPY app ./app

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8123

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8123"]