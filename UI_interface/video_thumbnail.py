"""
视频缩略图提取模块
使用 FFmpeg 提取视频首帧，替代 OpenCV
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def extract_first_frame_ffmpeg(video_path: str, output_width: int = 160, output_height: int = 96, 
                                ffmpeg_path: Optional[str] = None) -> Optional[bytes]:
    """
    使用 FFmpeg 提取视频首帧并调整大小
    
    Args:
        video_path: 视频文件路径
        output_width: 输出图像宽度
        output_height: 输出图像高度
        ffmpeg_path: FFmpeg 可执行文件路径（可选）
    
    Returns:
        成功返回图像字节数据（PNG格式），失败返回None
    """
    try:
        # 检查视频文件是否存在
        if not os.path.exists(video_path):
            print(f"[WARNING] 视频文件不存在: {video_path}")
            return None
        
        # 构建 ffmpeg 命令
        # -ss 0: 从第0秒开始
        # -i: 输入文件
        # -vframes 1: 只提取1帧
        # -vf scale: 调整大小，保持宽高比
        # -f image2pipe: 输出到管道
        # -vcodec png: 使用PNG编码
        # -: 输出到stdout
        
        cmd = ['ffmpeg']
        if ffmpeg_path:
            cmd = [os.path.join(ffmpeg_path, 'ffmpeg.exe') if os.name == 'nt' else os.path.join(ffmpeg_path, 'ffmpeg')]
        
        cmd.extend([
            '-ss', '0',  # 从开始位置
            '-i', video_path,  # 输入文件
            '-vframes', '1',  # 只提取1帧
            '-vf', f'scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2:color=0xc8c8c8',  # 缩放并居中，灰色背景
            '-f', 'image2pipe',  # 输出到管道
            '-vcodec', 'png',  # PNG编码
            '-'  # 输出到stdout
        ])
        
        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=10,
            check=False
        )
        
        if result.returncode == 0 and len(result.stdout) > 0:
            return result.stdout
        else:
            print(f"[WARNING] FFmpeg 提取首帧失败: {video_path}")
            if result.stderr:
                print(f"[ERROR] FFmpeg错误: {result.stderr.decode('utf-8', errors='ignore')}")
            return None
            
    except FileNotFoundError:
        print(f"[ERROR] 找不到 ffmpeg 命令")
        return None
    except subprocess.TimeoutExpired:
        print(f"[ERROR] FFmpeg 执行超时")
        return None
    except Exception as e:
        print(f"[ERROR] 提取视频首帧时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_first_frame_to_file(video_path: str, output_file: Optional[str] = None, 
                                output_width: int = 160, output_height: int = 96,
                                ffmpeg_path: Optional[str] = None) -> Optional[str]:
    """
    使用 FFmpeg 提取视频首帧到文件
    
    Args:
        video_path: 视频文件路径
        output_file: 输出文件路径（如果为None，则创建临时文件）
        output_width: 输出图像宽度
        output_height: 输出图像高度
        ffmpeg_path: FFmpeg 可执行文件路径（可选）
    
    Returns:
        成功返回输出文件路径，失败返回None
    """
    try:
        # 如果没有指定输出文件，创建临时文件
        if output_file is None:
            temp_fd, output_file = tempfile.mkstemp(suffix='.png')
            os.close(temp_fd)
        
        # 检查视频文件是否存在
        if not os.path.exists(video_path):
            print(f"[WARNING] 视频文件不存在: {video_path}")
            return None
        
        # 构建 ffmpeg 命令
        cmd = ['ffmpeg']
        if ffmpeg_path:
            cmd = [os.path.join(ffmpeg_path, 'ffmpeg.exe') if os.name == 'nt' else os.path.join(ffmpeg_path, 'ffmpeg')]
        
        cmd.extend([
            '-y',  # 覆盖输出文件
            '-ss', '0',  # 从开始位置
            '-i', video_path,  # 输入文件
            '-vframes', '1',  # 只提取1帧
            '-vf', f'scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2:color=0xc8c8c8',  # 缩放并居中，灰色背景
            output_file  # 输出文件
        ])
        
        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=10,
            check=False
        )
        
        if result.returncode == 0 and os.path.exists(output_file):
            return output_file
        else:
            print(f"[WARNING] FFmpeg 提取首帧失败: {video_path}")
            if result.stderr:
                print(f"[ERROR] FFmpeg错误: {result.stderr.decode('utf-8', errors='ignore')}")
            # 清理临时文件
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass
            return None
            
    except FileNotFoundError:
        print(f"[ERROR] 找不到 ffmpeg 命令")
        return None
    except subprocess.TimeoutExpired:
        print(f"[ERROR] FFmpeg 执行超时")
        return None
    except Exception as e:
        print(f"[ERROR] 提取视频首帧时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

