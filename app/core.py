import os
import io
import tempfile
import numpy as np
from PIL import Image, ImageOps
from moviepy.editor import ImageClip, concatenate_videoclips
from proglog import ProgressBarLogger # 关键：引入日志记录器

RESOLUTIONS = {
    "portrait": (1080, 1920),
    "landscape": (1920, 1080),
    "square": (1080, 1080)
}

# --- 自定义进度记录器 ---
class MyBarLogger(ProgressBarLogger):
    def __init__(self, callback=None):
        super().__init__(init_state=None, bars=None, ignored_bars=None,
                         logged_bars='all', min_time_interval=0, ignore_bars_under=0)
        self.callback = callback

    def callback_message(self, message):
        # 这里可以捕获文本日志，比如 "MoviePy - Writing video..."
        if self.callback:
            self.callback(message=message)

    def bars_callback(self, bar, attr, value, old_value=None):
        # 这里捕获进度条数值
        # 't' 代表时间合成进度, 'chunk' 代表写入文件进度
        # 我们主要关注 't' (index=0 of bars often)
        if self.callback:
            total = self.bars[bar]['total']
            if total > 0:
                percent = int((value / total) * 100)
                self.callback(percent=percent, stage=bar)

# --- 核心逻辑 ---

def resize_and_pad(img: Image.Image, target_size: tuple) -> np.ndarray:
    """保持原图比例，填充黑边 (同前)"""
    target_w, target_h = target_size
    img = ImageOps.exif_transpose(img)
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    img_w, img_h = img.size
    ratio = min(target_w / img_w, target_h / img_h)
    new_size = (int(img_w * ratio), int(img_h * ratio))
    
    img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
    background = Image.new('RGB', target_size, (0, 0, 0))
    paste_x = (target_w - new_size[0]) // 2
    paste_y = (target_h - new_size[1]) // 2
    background.paste(img_resized, (paste_x, paste_y))
    
    return np.array(background)

def create_video_from_images(
    image_bytes_list: list[bytes], 
    duration_per_image: float = 2.0,
    resolution_type: str = "portrait",
    progress_callback = None # 新增回调参数
) -> str:
    
    target_size = RESOLUTIONS.get(resolution_type, RESOLUTIONS["portrait"])
    clips = []
    temp_output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name

    try:
        # 阶段 1: 预处理图片 (假设占总进度的 10%)
        total_imgs = len(image_bytes_list)
        if progress_callback:
            progress_callback(percent=5, message="正在预处理图片...")

        for idx, img_bytes in enumerate(image_bytes_list):
            img = Image.open(io.BytesIO(img_bytes))
            img_np = resize_and_pad(img, target_size)
            clip = ImageClip(img_np).set_duration(duration_per_image)
            clips.append(clip)
            
            # 简单的预处理进度汇报
            if progress_callback:
                p = 5 + int((idx / total_imgs) * 10) # 5% -> 15%
                progress_callback(percent=p)

        # 阶段 2: 合成 (占剩余 85%)
        if progress_callback:
            progress_callback(percent=20, message="开始视频渲染...")

        final_clip = concatenate_videoclips(clips, method="compose")
        
        # 定义内部回调，映射到 20% - 100%
        def logger_callback(percent=None, message=None, stage=None):
            if percent is not None and progress_callback:
                # 映射 moviepy 0-100 到 全局 20-100
                final_p = 20 + int(percent * 0.8)
                progress_callback(percent=final_p, message="正在编码视频帧...")
        
        my_logger = MyBarLogger(logger_callback)

        final_clip.write_videofile(
            temp_output, 
            fps=24, 
            codec='libx264', 
            audio=False, 
            preset='ultrafast',
            threads=2, # WSL2 环境限制线程数防止卡死
            logger=my_logger # 注入 Logger
        )
        
        final_clip.close()
        
        if progress_callback:
            progress_callback(percent=100, message="完成！")
            
        return temp_output

    except Exception as e:
        if os.path.exists(temp_output):
            os.remove(temp_output)
        raise e