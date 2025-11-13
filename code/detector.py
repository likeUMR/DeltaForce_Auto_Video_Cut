"""
三角洲游戏击杀检测模块
基于模板匹配的击杀事件检测
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple
from config import Config


class KillDetector:
    def __init__(self, template_dir: str = Config.TEMPLATE_DIR, nearby_kills_merge: bool = Config.NEARBY_KILLS_MERGE):
        """初始化检测器，加载所有模板"""
        self.templates = []
        self.load_templates(template_dir)
        self.nearby_kills_merge = nearby_kills_merge  # 相近击杀片段合并: Ture 合并; False 不合并
        
    def load_templates(self, template_dir: str):
        """加载所有击杀图标模板，并自动调整尺寸"""
        print(f"\n[加载模板] 开始")
        print(f"  传入的模板目录参数: {template_dir}")
        print(f"  类型: {type(template_dir)}")
        
        template_path = Path(template_dir)
        print(f"  转换后的Path对象: {template_path}")
        print(f"  是否为绝对路径: {template_path.is_absolute()}")
        print(f"  路径是否存在: {template_path.exists()}")
        
        if not template_path.exists():
            # 尝试解析路径
            resolved_path = template_path.resolve()
            print(f"  解析后的路径: {resolved_path}")
            print(f"  解析后路径是否存在: {resolved_path.exists()}")
            
            if resolved_path.exists():
                template_path = resolved_path
                print(f"  ✓ 使用解析后的路径: {template_path}")
            else:
                raise FileNotFoundError(
                    f"模板目录不存在:\n"
                    f"  原始路径: {template_dir}\n"
                    f"  Path对象: {template_path}\n"
                    f"  解析路径: {resolved_path}"
                )
        
        print(f"\n[加载模板]")
        print(f"  模板目录: {template_path}")
        print(f"  绝对路径: {template_path.resolve()}")
        print(f"  ROI 区域尺寸: {Config.ROI_WIDTH} x {Config.ROI_HEIGHT}")
        print(f"  ROI 位置: ({Config.ROI_X}, {Config.ROI_Y})")
        
        loaded_count = 0
        
        # 获取要加载的模板文件列表
        # 优先使用Config.TEMPLATE_NAMES，如果为空或所有文件都不存在，则自动发现目录中的所有PNG/JPG文件
        template_names_to_load = Config.TEMPLATE_NAMES if Config.TEMPLATE_NAMES else []
        
        # 如果配置的模板列表为空，或者所有配置的模板都不存在，则自动发现
        if not template_names_to_load:
            # 自动发现目录中的所有图片文件
            template_files_found = list(template_path.glob("*.png")) + list(template_path.glob("*.jpg"))
            template_names_to_load = [f.name for f in template_files_found]
            print(f"  [自动发现] 找到 {len(template_names_to_load)} 个模板文件")
        else:
            # 检查配置的模板文件是否存在
            existing_templates = []
            missing_templates = []
            for template_name in template_names_to_load:
                if (template_path / template_name).exists():
                    existing_templates.append(template_name)
                else:
                    missing_templates.append(template_name)
            
            # 如果有缺失的模板，尝试自动发现
            if missing_templates:
                print(f"  ⚠ 配置的模板文件缺失: {missing_templates}")
                template_files_found = list(template_path.glob("*.png")) + list(template_path.glob("*.jpg"))
                found_names = [f.name for f in template_files_found]
                print(f"  [自动发现] 目录中的模板文件: {found_names}")
                # 使用找到的文件（优先使用配置中存在的，然后补充发现的）
                template_names_to_load = existing_templates + [name for name in found_names if name not in existing_templates]
        
        # 加载模板文件
        print(f"\n[加载模板] 开始加载 {len(template_names_to_load)} 个模板文件")
        for idx, template_name in enumerate(template_names_to_load, 1):
            print(f"\n  [{idx}/{len(template_names_to_load)}] 处理模板: {template_name}")
            template_file = template_path / template_name
            print(f"      完整路径: {template_file}")
            print(f"      路径是否存在: {template_file.exists()}")
            
            if not template_file.exists():
                print(f"      ⚠ 文件不存在: {template_name}")
                # 尝试列出目录中的所有文件
                if template_path.exists():
                    all_files = sorted(template_path.iterdir())
                    print(f"      目录中的所有文件 ({len(all_files)} 个):")
                    for f in all_files:
                        print(f"        - {f.name} ({'文件' if f.is_file() else '目录'})")
                continue
            
            # 检查文件大小
            file_size = template_file.stat().st_size
            print(f"      文件大小: {file_size} 字节")
            
            if file_size == 0:
                print(f"      ✗ 文件大小为0，跳过")
                continue
            
            # 尝试读取文件
            # 直接使用cv2.imdecode从字节流读取（解决中文路径问题，避免cv2.imread的警告）
            template = None
            
            try:
                # 使用Python的open读取文件（支持中文路径），然后用cv2.imdecode解码
                with open(template_file, 'rb') as f:
                    image_bytes = f.read()
                
                if image_bytes:
                    # 将字节转换为numpy数组
                    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                    
                    # 抑制libpng警告：重定向stderr
                    import os
                    import sys
                    from contextlib import redirect_stderr
                    from io import StringIO
                    
                    # 临时重定向stderr以抑制libpng警告
                    stderr_buffer = StringIO()
                    with redirect_stderr(stderr_buffer):
                        # 使用cv2.imdecode解码
                        template = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                    
                    if template is not None:
                        print(f"      ✓ 成功读取图像")
                    else:
                        print(f"      ✗ cv2.imdecode返回None，无法解码图像")
                else:
                    print(f"      ✗ 文件为空")
                
            except Exception as e:
                print(f"      ✗ 读取文件时发生异常: {e}")
                import traceback
                traceback.print_exc()
            
            if template is None:
                print(f"      ✗ 无法读取图像文件")
                print(f"      可能原因: 文件格式不支持、文件损坏、路径编码问题")
                # 尝试检查文件扩展名
                ext = template_file.suffix.lower()
                print(f"      文件扩展名: {ext}")
                if ext not in ['.png', '.jpg', '.jpeg']:
                    print(f"      ⚠ 警告: 扩展名可能不被支持")
                continue
            
            print(f"      ✓ 成功读取图像")
            original_h, original_w = template.shape[:2]
            print(f"      图像尺寸: {original_w} x {original_h}")
            
            # 检查模板是否过大，如果过大则缩放
            scale_factor = 1.0
            needs_resize = False
            
            if original_w > Config.ROI_WIDTH or original_h > Config.ROI_HEIGHT:
                # 计算缩放比例，确保模板不超过 ROI 的 80%
                scale_w = (Config.ROI_WIDTH * 0.8) / original_w
                scale_h = (Config.ROI_HEIGHT * 0.8) / original_h
                scale_factor = min(scale_w, scale_h)
                needs_resize = True
            
            if needs_resize:
                new_w = int(original_w * scale_factor)
                new_h = int(original_h * scale_factor)
                template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)
                print(f"  ⚠ {template_name}: {original_w}x{original_h} → {new_w}x{new_h} (自动缩放)")
            else:
                print(f"  ✓ {template_name}: {original_w}x{original_h}")
            
            self.templates.append({
                'name': template_name,
                'image': template,
                'height': template.shape[0],
                'width': template.shape[1],
                'original_size': (original_w, original_h),
                'scaled': needs_resize
            })
            loaded_count += 1
            print(f"      ✓ 模板已添加到列表 (当前已加载: {loaded_count} 个)")
        
        print(f"\n[加载模板] 加载完成")
        print(f"  尝试加载的模板数量: {len(template_names_to_load)}")
        print(f"  成功加载的模板数量: {loaded_count}")
        print(f"  当前模板列表长度: {len(self.templates)}")
        
        if len(self.templates) == 0:
            print(f"\n[ERROR] 没有成功加载任何模板！")
            print(f"  模板目录: {template_path}")
            print(f"  配置的模板列表: {Config.TEMPLATE_NAMES}")
            print(f"  尝试加载的模板: {template_names_to_load}")
            if template_path.exists():
                all_files = list(template_path.glob("*"))
                print(f"  目录中的所有文件: {[f.name for f in all_files]}")
            raise ValueError("没有成功加载任何模板！")
        
        print(f"\n  ✓ 共加载 {loaded_count} 个模板")
    
    def extract_roi(self, frame: np.ndarray) -> np.ndarray:
        """从帧中提取ROI区域"""
        x, y, w, h = Config.ROI_X, Config.ROI_Y, Config.ROI_WIDTH, Config.ROI_HEIGHT
        
        # 确保ROI不超出图像边界
        frame_h, frame_w = frame.shape[:2]
        x = max(0, min(x, frame_w - w))
        y = max(0, min(y, frame_h - h))
        
        return frame[y:y+h, x:x+w]
    
    def match_template(self, roi: np.ndarray) -> Tuple[bool, float, str]:
        """
        在ROI中匹配模板
        返回: (是否匹配成功, 最大相似度, 匹配的模板名称)
        """
        max_score = 0
        best_template_name = ""
        
        # 检查 ROI 尺寸
        roi_h, roi_w = roi.shape[:2]
        
        for template_info in self.templates:
            template = template_info['image']
            template_h, template_w = template.shape[:2]
            
            # 确保模板不大于 ROI
            if template_w > roi_w or template_h > roi_h:
                continue
            
            try:
                # 使用归一化相关系数匹配（对光照变化更鲁棒）
                result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > max_score:
                    max_score = max_val
                    best_template_name = template_info['name']
            except cv2.error as e:
                print(f"  ⚠ 模板 {template_info['name']} 匹配失败: {e}")
                continue
        
        is_match = max_score >= Config.MATCH_THRESHOLD
        return is_match, max_score, best_template_name
    
    def detect_kills(self, video_path: str) -> List[dict]:
        """
        检测视频中的所有击杀
        返回: [{timestamp: 时间戳, score: 相似度, template: 模板名, frame: 帧号}]
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"\n[视频信息]")
        print(f"  文件: {Path(video_path).name}")
        print(f"  分辨率: {video_width}x{video_height}")
        print(f"  帧率: {fps:.2f} fps")
        print(f"  总帧数: {total_frames}")
        print(f"  时长: {duration:.2f} 秒")
        
        # 检查分辨率
        if video_width != Config.VIDEO_WIDTH or video_height != Config.VIDEO_HEIGHT:
            print(f"  ⚠ 警告: 视频分辨率与配置不符")
            print(f"    配置: {Config.VIDEO_WIDTH}x{Config.VIDEO_HEIGHT}")
            print(f"    实际: {video_width}x{video_height}")
            print(f"    建议: 修改 config_deltaforce.py 中的分辨率设置")
        
        print(f"\n[开始检测]")
        print(f"  抽帧频率: {Config.SAMPLE_FPS} fps")
        print(f"  匹配阈值: {Config.MATCH_THRESHOLD}")
        print(f"  检测区域: ROI ({Config.ROI_X}, {Config.ROI_Y}) {Config.ROI_WIDTH}x{Config.ROI_HEIGHT}")
        
        detections = []
        frame_interval = int(fps / Config.SAMPLE_FPS)
        frame_count = 0
        processed_frames = 0
        
        print(f"\n检测进度:")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 按照设定的fps抽帧
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                
                # 提取ROI
                roi = self.extract_roi(frame)
                
                # 模板匹配
                is_match, score, template_name = self.match_template(roi)
                
                if is_match:
                    detections.append({
                        'timestamp': timestamp,
                        'score': score,
                        'template': template_name,
                        'frame': frame_count
                    })
                    print(f"  ✓ [{timestamp:7.2f}s] 检测到击杀 (相似度: {score:.3f}, 模板: {template_name})")
                
                processed_frames += 1
            
            frame_count += 1
            
            # 显示进度（每10秒显示一次）
            if frame_count % (int(fps + 0.5) * 10) == 0:
                progress = (frame_count / total_frames) * 100
                elapsed = frame_count / fps
                print(f"  [{elapsed:6.1f}s / {duration:.1f}s] 进度: {progress:5.1f}% | 已检测: {len(detections)} 个")
        
        cap.release()
        
        print(f"\n{'='*70}")
        print(f"检测完成!")
        print(f"  处理帧数: {processed_frames} 帧")
        print(f"  发现匹配: {len(detections)} 个")
        print(f"{'='*70}")
        
        return detections
    
    def merge_detections(self, detections: List[dict]) -> List[dict]:
        """
        合并时间窗口内的重复检测
        重要：不同击杀类型不会被合并，即使时间很近
        返回: 去重后的击杀事件列表
        """
        if not detections:
            return []

        # 按时间排序
        detections.sort(key=lambda x: x['timestamp'])

        merged = []
        current_group = [detections[0]]

        for i in range(1, len(detections)):
            current_detection = detections[i]
            last_in_group = current_group[-1]

            # 检查时间差是否在窗口内
            time_diff = current_detection['timestamp'] - last_in_group['timestamp']

            # 检查击杀类型是否相同
            same_type = current_detection['template'] == last_in_group['template']

            # 时间相近时，相同类型击杀或self.nearby_kills_merge==True的帧划归到同一击杀片段
            if time_diff < Config.TIME_WINDOW and (same_type or self.nearby_kills_merge):
                current_group.append(current_detection)
            else:
                # 否则，处理当前组并开始新组，并选取当前组第一帧为代表
                merged.append({
                    'start_timestamp': current_group[0]['timestamp'],
                    'end_timestamp': current_group[-1]['timestamp'],
                    'score': current_group[0]['score'],
                    'template': current_group[0]['template'],
                    'start_frame': current_group[0]['frame'],
                    'end_frame': current_group[-1]['frame']
                })
                current_group = [current_detection]

        # 处理最后一组
        if current_group:
            merged.append({
                'start_timestamp': current_group[0]['timestamp'],
                'end_timestamp': current_group[-1]['timestamp'],
                'score': current_group[0]['score'],
                'template': current_group[0]['template'],
                'start_frame': current_group[0]['frame'],
                'end_frame': current_group[-1]['frame']
            })

        print(f"\n[合并结果]")
        print(f"  原始检测: {len(detections)} 个")
        print(f"  合并后: {len(merged)} 个击杀事件")
        print(f"  时间窗口: {Config.TIME_WINDOW} 秒")
        print(f"  规则: 不同击杀类型不会合并")

        # 统计击杀类型
        from collections import Counter
        kill_types = Counter([e['template'] for e in merged])
        print(f"\n击杀类型统计:")
        for kill_type, count in kill_types.most_common():
            print(f"  • {kill_type}: {count} 次")

        print(f"\n击杀时间轴:")
        for idx, event in enumerate(merged, 1):
            timestamp = event['start_timestamp']
            minutes = int(timestamp // 60)
            seconds = timestamp % 60
            duration = event['end_timestamp'] - event['start_timestamp']
            template_short = event['template'].replace('.png', '').replace('elimination_', '')
            print(f"  击杀 {idx:2d}: {minutes:02d}:{seconds:05.2f} | 相似度: {event['score']:.3f} | 类型: {template_short} | 持续时间: {duration:.2f}s")

        return merged