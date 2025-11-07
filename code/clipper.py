"""
视频剪辑模块 - 三角洲游戏版本
使用 FFmpeg 剪辑击杀片段
"""
import ffmpeg
import os
import sys
import subprocess
from pathlib import Path
from typing import List
from config import Config


class VideoClipper:
    def __init__(self, input_video: str, output_dir: str, ffmpeg_path: str = None):
        self.input_video = input_video
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = ffmpeg_path
        
        # 如果指定了 ffmpeg 路径，设置环境变量
        if self.ffmpeg_path:
            os.environ['PATH'] = f"{self.ffmpeg_path}{os.pathsep}{os.environ.get('PATH', '')}"
            print(f"使用指定的 FFmpeg 路径: {self.ffmpeg_path}")
        
        # 测试 ffmpeg 是否可用
        self._test_ffmpeg()
    
    def _test_ffmpeg(self):
        """测试 FFmpeg 是否可用"""
        print("\n[FFmpeg 检测]")
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"  ✓ FFmpeg 可用: {version_line}")
            else:
                print(f"  ✗ FFmpeg 执行失败")
                print(f"  返回码: {result.returncode}")
        except FileNotFoundError:
            print(f"  ✗ 找不到 ffmpeg 命令")
            print(f"  请确保 FFmpeg 已安装或指定正确的路径")
            raise Exception("FFmpeg 未找到，无法继续")
        except Exception as e:
            print(f"  ✗ FFmpeg 测试失败: {e}")
            raise
    
    def get_video_duration(self) -> float:
        """获取视频总时长"""
        try:
            print(f"\n[获取视频信息] {Path(self.input_video).name}")
            probe = ffmpeg.probe(self.input_video)
            duration = float(probe['streams'][0]['duration'])
            print(f"  视频时长: {duration:.2f} 秒 ({int(duration//60)}分{int(duration%60)}秒)")
            return duration
        except Exception as e:
            print(f"  ✗ 获取视频信息失败: {e}")
            raise
    
    def clip_segment(self, start_time: float, end_time: float, output_file: str):
        """
        剪辑视频片段 - H.264 编码
        """
        duration = end_time - start_time
        
        # 构建 ffmpeg 命令
        cmd = [
            'ffmpeg',
            '-y',  # 覆盖输出文件
            '-ss', str(start_time),  # 开始时间
            '-i', self.input_video,  # 输入文件
            '-t', str(duration),  # 持续时间
            '-c:v', Config.OUTPUT_VIDEO_CODEC,  # 视频编码器
            '-crf', str(Config.OUTPUT_CRF),  # 质量
            '-preset', Config.OUTPUT_PRESET,  # 预设
            '-c:a', 'aac',  # 音频编码为 AAC
            '-b:a', '192k',  # 音频码率
            output_file  # 输出文件
        ]
        
        print(f"\n[剪辑片段]")
        print(f"  时间: {start_time:.2f}s - {end_time:.2f}s (时长: {duration:.2f}s)")
        print(f"  输出: {Path(output_file).name}")
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',  # 忽略无法解码的字符
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                # 检查文件是否真的生成了
                if Path(output_file).exists():
                    file_size = Path(output_file).stat().st_size / (1024 * 1024)  # MB
                    print(f"  ✓ 剪辑成功 ({file_size:.2f} MB)")
                    return True
                else:
                    print(f"  ✗ FFmpeg 执行成功但文件未生成")
                    return False
            else:
                print(f"  ✗ FFmpeg 执行失败 (返回码: {result.returncode})")
                if result.stderr:
                    # 只显示最后10行错误信息
                    error_lines = result.stderr.split('\n')
                    print(f"  错误信息:")
                    for line in error_lines[-10:]:
                        if line.strip():
                            print(f"    {line}")
                return False
                
        except FileNotFoundError as e:
            print(f"  ✗ 找不到文件: {e}")
            return False
            
        except subprocess.TimeoutExpired:
            print(f"  ✗ 剪辑超时（超过5分钟）")
            return False
            
        except Exception as e:
            print(f"  ✗ 未知错误: {type(e).__name__}: {e}")
            return False
    
    def clip_kills(self, kill_events: List[dict]) -> List[str]:
        """
        根据击杀事件列表剪辑视频
        智能处理重叠：如果两个片段会重叠，自动调整边界
        返回: 输出文件路径列表
        """
        try:
            video_duration = self.get_video_duration()
        except Exception as e:
            print(f"✗ 无法获取视频时长: {e}")
            return []
        
        output_files = []
        
        print(f"\n{'='*70}")
        print(f"开始剪辑 {len(kill_events)} 个击杀片段")
        print(f"  击杀前保留: {Config.CLIP_BEFORE} 秒")
        print(f"  击杀后保留: {Config.CLIP_AFTER} 秒")
        print(f"  智能避免重叠: ✓ 开启")
        print(f"{'='*70}")
        
        # 计算所有片段的时间范围
        segments = []
        for idx, event in enumerate(kill_events, 1):
            timestamp = event['timestamp']
            start_time = max(0, timestamp - Config.CLIP_BEFORE)
            end_time = min(video_duration, timestamp + Config.CLIP_AFTER)
            segments.append({
                'idx': idx,
                'event': event,
                'start': start_time,
                'end': end_time,
                'original_start': start_time,
                'original_end': end_time
            })
        
        # 检测并调整重叠
        for i in range(len(segments) - 1):
            current = segments[i]
            next_seg = segments[i + 1]
            
            # 检查是否重叠
            if current['end'] > next_seg['start']:
                overlap = current['end'] - next_seg['start']
                
                # 计算中点，从中点分割
                midpoint = (current['end'] + next_seg['start']) / 2
                
                # 调整边界
                current['end'] = midpoint
                next_seg['start'] = midpoint
                
                print(f"\n⚠ 检测到重叠:")
                print(f"  片段 {current['idx']} 与片段 {next_seg['idx']} 重叠 {overlap:.2f}秒")
                print(f"  已调整: 片段{current['idx']}结束于 {midpoint:.2f}s, 片段{next_seg['idx']}开始于 {midpoint:.2f}s")
        
        # 执行剪辑
        for segment in segments:
            idx = segment['idx']
            event = segment['event']
            start_time = segment['start']
            end_time = segment['end']
            
            # 生成输出文件名（包含时间戳和模板信息）
            template_name = Path(event['template']).stem  # 去掉扩展名
            output_file = self.output_dir / f"kill_{idx:03d}_{int(event['timestamp'])}s_{template_name}.mp4"
            
            print(f"\n[片段 {idx}/{len(kill_events)}]")
            print(f"  击杀时间: {event['timestamp']:.2f}s")
            print(f"  击杀类型: {event['template']}")
            print(f"  相似度: {event['score']:.3f}")
            
            # 显示是否调整过
            if start_time != segment['original_start'] or end_time != segment['original_end']:
                print(f"  ⚠ 时间已调整以避免重叠")
            
            # 执行剪辑
            if self.clip_segment(start_time, end_time, str(output_file)):
                output_files.append(str(output_file))
            else:
                print(f"  ⚠ 跳过此片段")
        
        print(f"\n{'='*70}")
        print(f"剪辑完成!")
        print(f"  成功: {len(output_files)}/{len(kill_events)}")
        if len(output_files) < len(kill_events):
            print(f"  失败: {len(kill_events) - len(output_files)}")
        print(f"{'='*70}")
        
        return output_files