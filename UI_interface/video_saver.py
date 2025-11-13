"""
视频保存模块
用于保存处理后的视频文件
"""
import os
import shutil
from pathlib import Path
from typing import Optional


def save_video_with_prefix(input_path: str, prefix: str = "[一杀一剪]") -> Optional[str]:
    """
    保存视频文件，在原文件名前添加前缀
    
    Args:
        input_path: 输入视频文件路径
        prefix: 文件名前缀，默认为"[一杀一剪]"
    
    Returns:
        成功返回输出文件路径，失败返回None
    """
    try:
        input_path_obj = Path(input_path)
        
        if not input_path_obj.exists():
            print(f"[ERROR] 输入文件不存在: {input_path}")
            return None
        
        # 获取文件目录和文件名
        output_dir = input_path_obj.parent
        original_name = input_path_obj.name
        name_without_ext = input_path_obj.stem
        extension = input_path_obj.suffix
        
        # 生成输出文件名：[一杀一剪]原文件名.扩展名
        output_name = f"{prefix}{original_name}"
        output_path = output_dir / output_name
        
        # 如果输出文件已存在，先删除（替换）
        if output_path.exists():
            print(f"[INFO] 输出文件已存在，将替换: {output_path}")
            try:
                output_path.unlink()
            except Exception as e:
                print(f"[ERROR] 删除已存在文件失败: {e}")
                return None
        
        # 复制文件
        print(f"[INFO] 正在保存视频: {input_path} -> {output_path}")
        shutil.copy2(input_path, output_path)
        
        # 验证文件是否成功复制
        if output_path.exists() and output_path.stat().st_size > 0:
            print(f"[INFO] 视频保存成功: {output_path}")
            return str(output_path)
        else:
            print(f"[ERROR] 视频保存失败: 文件不存在或大小为0")
            return None
            
    except Exception as e:
        print(f"[ERROR] 保存视频时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

