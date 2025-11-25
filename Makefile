# 变量定义
PYTHON = python
PORT = 8123
APP_MODULE = app.main:app
IMAGE_NAME = pic-to-vid
CONTAINER_NAME = pic-to-vid-container

.PHONY: help install run clean docker-build docker-up docker-down docker-logs

help:  ## 显示帮助信息
	@echo "========================================"
	@echo "   PIC-TO-VID 管理面板 (WSL2/Linux)"
	@echo "========================================"
	@echo "本地开发:"
	@echo "  make install      - 安装本地依赖 (pip)"
	@echo "  make run          - 本地运行 (热重载)"
	@echo "  make clean        - 清理缓存文件"
	@echo ""
	@echo "Docker 管理 (Compose V2):"
	@echo "  make docker-up    - 构建并启动服务"
	@echo "  make docker-down  - 停止服务"
	@echo "  make docker-logs  - 查看实时日志"
	@echo "  make docker-build - 强制无缓存重构"

# --- 本地开发命令 ---
install:
	$(PYTHON) -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

run:
	$(PYTHON) -m uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port $(PORT)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -f *.mp4

# --- Docker 命令 ---
docker-build: ## 强制重新构建
	docker compose build 

docker-up: ## 启动服务
	docker compose up -d --build
	@echo "------------------------------------------------"
	@echo "Pic-to-Vid 已启动! 访问: http://localhost:$(PORT)"
	@echo "------------------------------------------------"

docker-down: ## 停止服务
	docker compose down --remove-orphans

docker-logs: ## 查看日志
	docker compose logs -f