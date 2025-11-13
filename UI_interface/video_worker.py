"""
视频处理工作线程
在后台线程中处理视频，避免阻塞UI
"""
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional
import sys
from pathlib import Path

# 添加code目录到路径
current_dir = Path(__file__).parent.parent
code_dir = current_dir / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from UI_interface.video_processor import VideoProcessor


class VideoWorker(QThread):
    """视频处理工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(float, str)  # progress, message
    finished = pyqtSignal(dict)  # result dict
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, video_path: str, output_dir: Optional[str] = None,
                 final_output_path: Optional[str] = None,
                 template_dir: Optional[str] = None, ffmpeg_path: Optional[str] = None):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.final_output_path = final_output_path
        self.template_dir = template_dir
        self.ffmpeg_path = ffmpeg_path
        self.processor = None
        
    def run(self):
        """执行视频处理"""
        try:
            # 创建处理器
            self.processor = VideoProcessor(
                template_dir=self.template_dir,
                ffmpeg_path=self.ffmpeg_path
            )
            
            # 设置进度回调
            self.processor.set_progress_callback(self._on_progress)
            
            # 处理视频
            result = self.processor.process_video(
                self.video_path,
                output_dir=self.output_dir,
                final_output_path=self.final_output_path
            )
            
            # 发送完成信号
            self.finished.emit(result)
            
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] VideoWorker发生错误: {error_msg}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(error_msg)
    
    def _on_progress(self, progress: float, message: str):
        """进度回调"""
        self.progress_updated.emit(progress, message)

