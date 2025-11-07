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
    def __init__(self, template_dir: str = Config.TEMPLATE_DIR):
        """初始化检测器，加载所有模板"""
        self.templates = []
        self.load_templates(template_dir)
        
    def load_templates(self, template_dir: str):
        """加载所有击杀图标模板，并自动调整尺寸"""
        template_path = Path(template_dir)
        if not template_path.exists():
            raise FileNotFoundError(f"模板目录不存在: {template_dir}")
        
        print(f"\n[加载模板]")
        print(f"  模板目录: {template_dir}")
        print(f"  ROI 区域尺寸: {Config.ROI_WIDTH} x {Config.ROI_HEIGHT}")
        print(f"  ROI 位置: ({Config.ROI_X}, {Config.ROI_Y})")
        
        loaded_count = 0
        for template_name in Config.TEMPLATE_NAMES:
            template_file = template_path / template_name
            
            if not template_file.exists():
                print(f"  ⚠ 文件不存在: {template_name}")
                continue
                
            template = cv2.imread(str(template_file))
            if template is None:
                print(f"  ✗ 无法读取: {template_name}")
                continue
            
            original_h, original_w = template.shape[:2]
            
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
        
        if len(self.templates) == 0:
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
            if frame_count % (fps * 10) == 0:
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
            
            # 只有时间接近 且 类型相同 才合并
            if time_diff <= Config.TIME_WINDOW and same_type:
                current_group.append(current_detection)
            else:
                # 否则，处理当前组并开始新组
                # 选择相似度最高的作为代表
                best = max(current_group, key=lambda x: x['score'])
                merged.append(best)
                current_group = [current_detection]
        
        # 处理最后一组
        if current_group:
            best = max(current_group, key=lambda x: x['score'])
            merged.append(best)
        
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
            timestamp = event['timestamp']
            minutes = int(timestamp // 60)
            seconds = timestamp % 60
            template_short = event['template'].replace('.png', '').replace('elimination_', '')
            print(f"  击杀 {idx:2d}: {minutes:02d}:{seconds:05.2f} | 相似度: {event['score']:.3f} | 类型: {template_short}")
        
        return merged