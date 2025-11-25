# Pic-to-Vid (极光版) 🎬

> 将碎片化的图片瞬间“熔炼”成适合微信分享的 MP4 视频。

![Python](https://img.shields.io/badge/Python-3.13-blue) ![MoviePy](https://img.shields.io/badge/Video-MoviePy-ff0080) ![Docker](https://img.shields.io/badge/Docker-Compose_V2-2496ED)

## ✨ 核心特性

- **多尺寸适配**：支持竖屏 (9:16)、横屏 (16:9)、方屏 (1:1) 等多种模式。
- **智能检测**：根据上传的图片自动推荐最佳分辨率。
- **无损画面**：图片**绝不裁剪**，采用智能黑边/模糊填充，保留画面完整性。
- **节奏掌控**：自由调节每张图片的播放时长（0.5s - 10s）。
- **微信友好**：生成的 MP4 编码经过优化，微信内直接播放，无需转码。

## 🚀 快速开始 (Docker)

本项目专为 WSL2 + Docker Compose V2 环境设计。

### 1. 启动服务

```bash
make docker-up
```

2. 使用工具
   打开浏览器访问：http://localhost:8123
3. 常用命令
   code
   Bash
   make docker-logs # 查看日志
   make docker-down # 停止服务
   make clean # 清理临时文件
   🛠️ 本地开发
   需要安装 ffmpeg 系统库。
   code
   Bash

# 1. 安装 Python 依赖

make install

# 2. 启动服务

make run
License
MIT License
