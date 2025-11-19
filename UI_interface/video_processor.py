"""
视频处理服务模块
集成检测和剪辑功能，提供进度回调
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Callable, Optional, Dict, List

# 尝试导入ffmpeg-python，如果失败则使用subprocess作为备选
try:
    import ffmpeg
    FFMPEG_PYTHON_AVAILABLE = hasattr(ffmpeg, 'probe')
except (ImportError, AttributeError):
    FFMPEG_PYTHON_AVAILABLE = False
    ffmpeg = None

# 添加code目录到路径
current_dir = Path(__file__).parent.parent
code_dir = current_dir / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

try:
    from detector import KillDetector
    from clipper import VideoClipper
    from config import Config
except ImportError as e:
    print(f"[ERROR] 无法导入处理模块: {e}")
    raise


class VideoProcessor:
    """视频处理服务类"""
    
    def __init__(self, template_dir: Optional[str] = None, ffmpeg_path: Optional[str] = None):
        """
        初始化视频处理器
        
        Args:
            template_dir: 模板目录路径，如果为None则使用Config中的默认路径
            ffmpeg_path: FFmpeg路径，如果为None则使用系统PATH中的ffmpeg
        """
        # 处理模板目录路径（相对路径转绝对路径）
        if template_dir:
            self.template_dir = template_dir
        else:
            # 使用Config中的路径，转换为绝对路径
            template_path_str = Config.TEMPLATE_DIR
            template_path = Path(template_path_str)
            
            if template_path.is_absolute():
                self.template_dir = str(template_path)
            else:
                # 相对路径，需要解析
                # Config中的路径是相对于code目录的，如 "..\match_templates\game_events"
                # 在Windows上，需要正确处理路径分隔符和..符号
                
                # 方法1: 如果路径以..开头，直接构建相对于code_dir.parent的路径
                if template_path_str.startswith('..'):
                    # 移除开头的..，然后构建路径
                    # 例如: "..\match_templates\game_events" -> "match_templates\game_events"
                    remaining_path = template_path_str.replace('..\\', '').replace('../', '')
                    resolved_path = (code_dir.parent / remaining_path).resolve()
                else:
                    # 相对于code目录
                    resolved_path = (code_dir / template_path_str).resolve()
                
                # 确保路径存在
                if not resolved_path.exists():
                    # 尝试直接使用项目根目录下的路径（备用方案）
                    alt_path = code_dir.parent / "match_templates" / "game_events"
                    if alt_path.exists():
                        resolved_path = alt_path.resolve()
                    else:
                        # 打印调试信息
                        print(f"[DEBUG] 尝试的路径1: {resolved_path}")
                        print(f"[DEBUG] 尝试的路径2: {alt_path}")
                        print(f"[DEBUG] code_dir: {code_dir}")
                        print(f"[DEBUG] code_dir.parent: {code_dir.parent}")
                        raise FileNotFoundError(
                            f"模板目录不存在。\n"
                            f"尝试路径1: {resolved_path}\n"
                            f"尝试路径2: {alt_path}\n"
                            f"请检查模板目录是否存在。"
                        )
                
                self.template_dir = str(resolved_path)
        
        self.ffmpeg_path = ffmpeg_path
        
        # 初始化检测器（延迟加载，避免在导入时就加载模板）
        self.detector: Optional[KillDetector] = None
        self.clipper: Optional[VideoClipper] = None
        
        # 进度回调函数
        self.progress_callback: Optional[Callable[[float, str], None]] = None
        
    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """
        设置进度回调函数
        
        Args:
            callback: 回调函数，参数为(progress: float, message: str)
                progress: 进度值 0.0-1.0
                message: 进度消息
        """
        self.progress_callback = callback
    
    def _report_progress(self, progress: float, message: str):
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(progress, message)
    
    def get_video_info(self, video_path: str) -> Dict[str, any]:
        """
        获取视频信息（使用FFmpeg）
        
        Returns:
            {
                'duration': 时长（秒）,
                'width': 宽度,
                'height': 高度,
                'fps': 帧率,
                'duration_str': 时长字符串（HH:MM:SS）
            }
        """
        try:
            probe = None
            
            # 方法1: 使用ffmpeg-python
            if FFMPEG_PYTHON_AVAILABLE:
                try:
                    probe = ffmpeg.probe(video_path)
                except Exception as e:
                    print(f"[DEBUG] ffmpeg.probe失败: {e}，尝试使用ffprobe命令")
            
            # 方法2: 使用ffprobe命令（备选方案）
            if probe is None:
                cmd = ['ffprobe', '-v', 'error', '-print_format', 'json',
                       '-show_format', '-show_streams', video_path]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=30
                )
                
                if result.returncode == 0:
                    probe = json.loads(result.stdout)
                else:
                    raise ValueError(f"ffprobe执行失败: {result.stderr}")
            
            # 查找视频流
            video_stream = None
            for stream in probe.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise ValueError("未找到视频流")
            
            # 获取视频信息
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            
            # 获取帧率（可能是分数形式，如 "30/1"）
            r_frame_rate = video_stream.get('r_frame_rate', '0/1')
            if '/' in r_frame_rate:
                num, den = map(int, r_frame_rate.split('/'))
                fps = num / den if den > 0 else 0
            else:
                fps = float(r_frame_rate) if r_frame_rate else 0
            
            # 获取时长
            duration_str_raw = video_stream.get('duration') or probe.get('format', {}).get('duration', '0')
            duration = float(duration_str_raw) if duration_str_raw else 0
            
            # 格式化时长
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            return {
                'duration': duration,
                'width': width,
                'height': height,
                'fps': fps,
                'duration_str': duration_str
            }
        except Exception as e:
            print(f"[ERROR] 获取视频信息失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'duration': 0,
                'width': 0,
                'height': 0,
                'fps': 0,
                'duration_str': '00:00:00'
            }
    
    def initialize_detector(self):
        """初始化检测器（延迟加载）"""
        if self.detector is None:
            print(f"\n[VideoProcessor] 开始初始化检测器")
            print(f"[VideoProcessor] 模板目录: {self.template_dir}")
            print(f"[VideoProcessor] 模板目录类型: {type(self.template_dir)}")
            
            template_path = Path(self.template_dir)
            print(f"[VideoProcessor] Path对象: {template_path}")
            print(f"[VideoProcessor] 是否为绝对路径: {template_path.is_absolute()}")
            print(f"[VideoProcessor] 路径是否存在: {template_path.exists()}")
            
            if template_path.exists():
                template_files = list(template_path.glob("*.png")) + list(template_path.glob("*.jpg"))
                print(f"[VideoProcessor] 目录中的PNG/JPG文件数量: {len(template_files)}")
                print(f"[VideoProcessor] 目录中的模板文件: {[f.name for f in template_files]}")
                print(f"[VideoProcessor] Config.TEMPLATE_NAMES: {Config.TEMPLATE_NAMES}")
                
                # 检查每个配置的模板文件是否存在
                for template_name in Config.TEMPLATE_NAMES:
                    template_file = template_path / template_name
                    exists = template_file.exists()
                    print(f"[VideoProcessor]   - {template_name}: {'存在' if exists else '不存在'} ({template_file})")
            else:
                print(f"[VideoProcessor] ⚠ 警告: 模板目录不存在！")
                # 尝试解析路径
                try:
                    resolved = template_path.resolve()
                    print(f"[VideoProcessor] 解析后的路径: {resolved}")
                    print(f"[VideoProcessor] 解析后路径是否存在: {resolved.exists()}")
                except Exception as e:
                    print(f"[VideoProcessor] 解析路径时出错: {e}")
            
            print(f"[VideoProcessor] 创建KillDetector实例...")
            try:
                self.detector = KillDetector(
                    template_dir=self.template_dir,
                    nearby_kills_merge=Config.NEARBY_KILLS_MERGE
                )
                print(f"[VideoProcessor] ✓ KillDetector初始化成功")
            except Exception as e:
                print(f"[VideoProcessor] ✗ KillDetector初始化失败: {e}")
                import traceback
                traceback.print_exc()
                raise
    
    def process_video(self, video_path: str, output_dir: Optional[str] = None, 
                     final_output_path: Optional[str] = None) -> Dict[str, any]:
        """
        处理视频：检测击杀并剪辑
        
        Args:
            video_path: 输入视频路径
            output_dir: 输出目录，如果为None则使用视频所在目录（用于存放中间文件）
            final_output_path: 最终输出文件路径，如果提供则：
                - 将最终输出文件复制/移动到该路径
                - 删除所有中间文件（kill_xxx.mp4和merged_video_segmentsNum_xxx.mp4）
        
        Returns:
            {
                'success': bool,
                'output_file': str,  # 最终输出文件路径
                'output_files': List[str],  # 所有输出文件列表（包括中间文件）
                'kill_count': int,  # 检测到的击杀数量
                'error': str  # 错误信息（如果有）
            }
        """
        try:
            # 确定输出目录（用于存放中间文件）
            if output_dir is None:
                output_dir = str(Path(video_path).parent)
            
            # 初始化检测器
            self.initialize_detector()
            
            # 步骤1: 检测击杀（带进度回调）
            self._report_progress(0.1, "开始检测击杀事件...")
            detections = self._detect_kills_with_progress(video_path)
            
            if not detections:
                self._report_progress(1.0, "未检测到击杀事件")
                return {
                    'success': False,
                    'output_file': None,
                    'output_files': [],
                    'kill_count': 0,
                    'error': '未检测到击杀事件'
                }
            
            # 步骤2: 合并重复检测
            self._report_progress(0.4, f"合并检测结果（检测到{len(detections)}个匹配点）...")
            kill_events = self.detector.merge_detections(detections)
            self._report_progress(0.5, f"合并后得到{len(kill_events)}个击杀事件")
            
            # 步骤3: 剪辑视频（带进度回调）
            self._report_progress(0.5, "开始剪辑视频片段...")
            output_files = self._clip_kills_with_progress(video_path, output_dir, kill_events)
            
            if not output_files:
                return {
                    'success': False,
                    'output_file': None,
                    'output_files': [],
                    'kill_count': len(kill_events),
                    'error': '剪辑失败'
                }
            
            # 步骤4: 合并片段（可选）- 如果有多个片段，自动合并
            final_output = None
            if len(output_files) > 1:
                self._report_progress(0.95, "合并视频片段...")
                final_output = self._merge_segments(output_dir, output_files)
            
            # 如果没有合并文件，使用第一个输出文件作为最终输出
            if not final_output and output_files:
                final_output = output_files[0]
            
            # 步骤5: 如果指定了final_output_path，复制最终文件并清理中间文件
            if final_output_path and final_output:
                self._report_progress(0.98, "保存最终文件并清理中间文件...")
                final_output = self._save_final_output_and_cleanup(
                    final_output, final_output_path, output_files, output_dir
                )
            
            self._report_progress(1.0, "处理完成")
            
            return {
                'success': True,
                'output_file': final_output or (output_files[0] if output_files else None),
                'output_files': output_files,
                'kill_count': len(kill_events),
                'error': None
            }
            
        except Exception as e:
            print(f"[ERROR] 处理视频时发生错误: {e}")
            import traceback
            traceback.print_exc()
            self._report_progress(1.0, f"处理失败: {str(e)}")
            return {
                'success': False,
                'output_file': None,
                'output_files': [],
                'kill_count': 0,
                'error': str(e)
            }
    
    def _detect_kills_with_progress(self, video_path: str) -> List[dict]:
        """检测击杀（带进度回调）"""
        # 局部导入cv2，因为detector模块需要它来读取视频帧和处理图像
        import cv2
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = int(fps / Config.SAMPLE_FPS)
        
        detections = []
        frame_count = 0
        processed_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 按照设定的fps抽帧
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                
                # 提取ROI
                roi = self.detector.extract_roi(frame)
                
                # 模板匹配
                is_match, score, template_name = self.detector.match_template(roi)
                
                if is_match:
                    detections.append({
                        'timestamp': timestamp,
                        'score': score,
                        'template': template_name,
                        'frame': frame_count
                    })
                
                processed_frames += 1
                
                # 报告进度（每处理一定帧数报告一次）
                if processed_frames % 10 == 0 and total_frames > 0:
                    progress = 0.1 + (frame_count / total_frames) * 0.3  # 检测阶段占30%进度
                    self._report_progress(progress, f"检测中... ({len(detections)}个击杀)")
            
            frame_count += 1
        
        cap.release()
        
        # 检测完成，报告进度
        self._report_progress(0.4, f"检测完成，发现{len(detections)}个匹配点")
        
        return detections
    
    def _clip_kills_with_progress(self, video_path: str, output_dir: str, kill_events: List[dict]) -> List[str]:
        """剪辑击杀片段（带进度回调）"""
        if self.clipper is None:
            self.clipper = VideoClipper(video_path, output_dir, ffmpeg_path=self.ffmpeg_path)
        
        try:
            video_duration = self.clipper.get_video_duration()
        except Exception as e:
            print(f"✗ 无法获取视频时长: {e}")
            return []
        
        output_files = []
        
        # 计算所有片段的时间范围
        segments = []
        for idx, event in enumerate(kill_events, 1):
            start_timestamp = event['start_timestamp']
            end_timestamp = event['end_timestamp']
            start_time = max(0, start_timestamp - Config.CLIP_BEFORE)
            end_time = min(video_duration, end_timestamp + Config.CLIP_AFTER)
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
            
            if current['end'] > next_seg['start']:
                midpoint = (current['end'] + next_seg['start']) / 2
                current['end'] = midpoint
                next_seg['start'] = midpoint
        
        # 执行剪辑
        total_segments = len(segments)
        for idx, segment in enumerate(segments):
            segment_idx = segment['idx']
            event = segment['event']
            start_time = segment['start']
            end_time = segment['end']
            
            # 生成输出文件名
            template_name = Path(event['template']).stem
            output_file = Path(output_dir) / f"kill_{segment_idx:03d}_{int(event['start_timestamp'])}s_{template_name}.mp4"
            
            # 报告进度
            clip_progress = 0.5 + (idx / total_segments) * 0.4  # 剪辑阶段占40%进度
            self._report_progress(clip_progress, f"剪辑片段 {segment_idx}/{total_segments}...")
            
            # 执行剪辑
            if self.clipper.clip_segment(start_time, end_time, str(output_file)):
                output_files.append(str(output_file))
        
        return output_files
    
    def _merge_segments(self, output_dir: str, output_files: List[str]) -> Optional[str]:
        """合并视频片段"""
        if not output_files or len(output_files) <= 1:
            return None
        
        try:
            # 使用clipper的merge_kill_segments方法
            success = self.clipper.merge_kill_segments(output_files)
            if success:
                # 合并后的文件命名规则：merged_video_segmentsNum_{数量}.mp4
                merged_file = Path(output_dir) / f"merged_video_segmentsNum_{len(output_files) - 1}.mp4"
                if merged_file.exists():
                    return str(merged_file)
            return None
        except Exception as e:
            print(f"[ERROR] 合并片段失败: {e}")
            return None
    
    def _save_final_output_and_cleanup(self, source_file: str, final_output_path: str, 
                                      all_output_files: List[str], output_dir: str) -> str:
        """
        保存最终输出文件并清理中间文件
        
        Args:
            source_file: 源文件路径（最终处理结果）
            final_output_path: 最终输出文件路径
            all_output_files: 所有中间输出文件列表
            output_dir: 输出目录（用于查找需要删除的文件）
        
        Returns:
            最终输出文件路径
        """
        import shutil
        
        try:
            final_path = Path(final_output_path)
            
            # 确保输出目录存在
            final_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果最终文件已存在，先删除
            if final_path.exists():
                print(f"[DEBUG] 最终输出文件已存在，将替换: {final_path}")
                final_path.unlink()
            
            # 复制源文件到最终输出路径
            print(f"[DEBUG] 复制最终文件: {source_file} -> {final_output_path}")
            shutil.copy2(source_file, final_output_path)
            
            # 验证文件是否成功复制
            if not final_path.exists() or final_path.stat().st_size == 0:
                raise ValueError("最终文件复制失败或文件大小为0")
            
            print(f"[DEBUG] ✓ 最终文件保存成功: {final_output_path}")
            
            # 清理中间文件
            print(f"[DEBUG] 开始清理中间文件...")
            deleted_count = 0
            
            # 删除所有中间输出文件（kill_xxx.mp4）
            for output_file in all_output_files:
                file_path = Path(output_file)
                if file_path.exists() and file_path != final_path:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        print(f"[DEBUG]   删除: {file_path.name}")
                    except Exception as e:
                        print(f"[WARNING] 无法删除中间文件 {file_path}: {e}")
            
            # 删除合并文件（merged_video_segmentsNum_xxx.mp4）
            for merged_file in Path(output_dir).glob("merged_video_segmentsNum_*.mp4"):
                if merged_file.exists() and merged_file != final_path:
                    try:
                        merged_file.unlink()
                        deleted_count += 1
                        print(f"[DEBUG]   删除: {merged_file.name}")
                    except Exception as e:
                        print(f"[WARNING] 无法删除合并文件 {merged_file}: {e}")
            
            print(f"[DEBUG] ✓ 清理完成，共删除 {deleted_count} 个中间文件")
            
            return str(final_path)
            
        except Exception as e:
            print(f"[ERROR] 保存最终文件或清理中间文件时发生错误: {e}")
            import traceback
            traceback.print_exc()
            # 即使清理失败，也返回最终路径（如果文件已复制）
            if Path(final_output_path).exists():
                return final_output_path
            # 否则返回源文件路径
            return source_file

