"""
三角洲游戏 - 击杀自动剪辑工具
主程序入口
"""
import json
import os
from pathlib import Path
from detector import KillDetector
from clipper import VideoClipper


def main():
    # ===== 配置区域 - 修改这里的路径 =====
    
    # 输入视频路径（修改成你的视频文件路径）
    VIDEO_PATH = r"C:\Users\admin\Desktop\Delta force\test_video\test_video_1.mp4"
    
    # 输出目录
    OUTPUT_DIR = r"C:\Users\admin\Desktop\Delta force\output_video"
    
    # 模板目录
    TEMPLATE_DIR = r"..\match_templates\game_events"
    
    # FFmpeg 路径（如果系统PATH中有ffmpeg可以设为None）
    current_dir = Path(__file__).parent
    FFMPEG_PATH = str(current_dir / "ffmpeg" / "bin")  # 或者设为 None

    # ============== 参数设置 ==============
    nearby_kills_merge = True  # 时间相近的击杀合并至同一片段（无论击杀类型）
    segment_merge_mode = True  # 是否将剪辑的片段进行合并, True: 额外输出片段合并视频, False: 不额外输出片段合并视频
    
    # ====================================
    
    print("=" * 70)
    print(" " * 15 + "三角洲游戏 - 击杀自动剪辑工具")
    print("=" * 70)
    
    # 检查 FFmpeg
    print("\n[步骤 1/5] 环境检查")
    print("=" * 70)
    
    ffmpeg_exe = Path(FFMPEG_PATH) / "ffmpeg.exe" if FFMPEG_PATH else None
    if FFMPEG_PATH and ffmpeg_exe and not ffmpeg_exe.exists():
        print(f"✗ 找不到 FFmpeg: {ffmpeg_exe}")
        print(f"\n解决方案：")
        print(f"  方案1: 下载 FFmpeg 并放到指定位置")
        print(f"         https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip")
        print(f"  方案2: 如果系统已安装FFmpeg，设置 FFMPEG_PATH = None")
        return
    elif FFMPEG_PATH:
        print(f"✓ FFmpeg 路径: {FFMPEG_PATH}")
        os.environ['PATH'] = f"{FFMPEG_PATH};{os.environ.get('PATH', '')}"
    else:
        print(f"✓ 使用系统 FFmpeg")
    
    # 检查输入视频
    if not Path(VIDEO_PATH).exists():
        print(f"✗ 视频文件不存在: {VIDEO_PATH}")
        print(f"  请在 main.py 中修改 VIDEO_PATH 为正确的视频路径")
        return
    else:
        video_size = Path(VIDEO_PATH).stat().st_size / (1024 * 1024)
        print(f"✓ 输入视频: {Path(VIDEO_PATH).name} ({video_size:.1f} MB)")
    
    # 检查模板目录
    if not Path(TEMPLATE_DIR).exists():
        print(f"✗ 模板目录不存在: {TEMPLATE_DIR}")
        print(f"  请创建模板目录并放入击杀图标模板")
        return
    else:
        template_count = len(list(Path(TEMPLATE_DIR).glob("*.png"))) + len(list(Path(TEMPLATE_DIR).glob("*.jpg")))
        print(f"✓ 模板目录: {Path(TEMPLATE_DIR).name} (找到 {template_count} 个模板)")
    
    print(f"✓ 输出目录: {OUTPUT_DIR}")
    
    # 步骤 2: 加载模板
    print("\n[步骤 2/5] 加载击杀图标模板")
    print("=" * 70)
    try:
        detector = KillDetector(template_dir=TEMPLATE_DIR, nearby_kills_merge=nearby_kills_merge)
    except Exception as e:
        print(f"✗ 加载模板失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 步骤 3: 检测击杀
    print("\n[步骤 3/5] 检测视频中的击杀画面")
    print("=" * 70)
    try:
        detections = detector.detect_kills(VIDEO_PATH)
    except Exception as e:
        print(f"✗ 检测失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not detections:
        print("\n" + "!" * 70)
        print(" " * 20 + "未检测到任何击杀事件！")
        print("!" * 70)
        print("\n可能的原因：")
        print("  1. 视频中没有击杀画面")
        print("  2. 模板图片与视频中的击杀图标不匹配")
        print("  3. 匹配阈值设置过高")
        print("  4. ROI区域设置不正确")
        print("\n建议：")
        print("  1. 运行 debug_detector_deltaforce.py 查看可视化调试")
        print("  2. 在 config_deltaforce.py 中降低 MATCH_THRESHOLD (如改为 0.6)")
        print("  3. 检查 ROI 区域设置是否覆盖击杀图标")
        print("  4. 确认视频分辨率与配置一致 (当前设置: 2304x1440)")
        return
    
    # 步骤 4: 合并重复检测
    print("\n[步骤 4/5] 合并重复检测结果")
    print("=" * 70)
    kill_events = detector.merge_detections(detections)
    
    # 保存检测日志
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = output_dir / "detection_log.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'video': str(VIDEO_PATH),
            'video_name': Path(VIDEO_PATH).name,
            'total_detections': len(detections),
            'kill_events': len(kill_events),
            'events': kill_events,
            'config': {
                'resolution': f"{detector.templates[0] if detector.templates else 'N/A'}",
                'roi': f"({detector.extract_roi.__code__.co_consts})",
                'threshold': 'See config_deltaforce.py'
            }
        }, f, indent=2, ensure_ascii=False)
    print(f"✓ 检测日志已保存: {log_file.name}")
    
    # 步骤 5: 剪辑视频
    print("\n[步骤 5/5] 剪辑击杀片段")
    print("=" * 70)
    try:
        clipper = VideoClipper(VIDEO_PATH, OUTPUT_DIR, ffmpeg_path=FFMPEG_PATH)
        output_files = clipper.clip_kills(kill_events)
    except Exception as e:
        print(f"✗ 剪辑失败: {e}")
        import traceback
        traceback.print_exc()
        return

    if segment_merge_mode:
        print("\n" + "=" * 70)
        print("拼接击杀片段")
        print("=" * 70)
        clipper.merge_kill_segments(output_files)
    
    # 完成
    print("\n" + "=" * 70)
    print(" " * 28 + "✓ 处理完成！")
    print("=" * 70)
    
    print(f"\n📊 统计信息:")
    print(f"  • 视频文件: {Path(VIDEO_PATH).name}")
    print(f"  • 检测到的匹配点: {len(detections)} 个")
    print(f"  • 合并后的击杀事件: {len(kill_events)} 个")
    print(f"  • 成功剪辑的片段: {len(output_files) - 1 if segment_merge_mode else len(output_files)} 个")
    print(f"  • 拼接文件: {len(output_files) - 1 if segment_merge_mode else 0} 个")
    
    # 按击杀类型统计
    if kill_events:
        from collections import Counter
        kill_types = Counter([e['template'] for e in kill_events])
        print(f"\n📈 击杀类型统计:")
        for kill_type, count in kill_types.most_common():
            print(f"  • {kill_type}: {count} 次")
    
    print(f"\n📁 输出位置:")
    print(f"  • 视频片段: {OUTPUT_DIR}")
    print(f"  • 检测日志: {log_file}")
    
    if output_files:
        print(f"\n🎬 生成的视频片段:")
        total_size = 0
        for idx, file in enumerate(output_files, 1):
            file_size = Path(file).stat().st_size / (1024 * 1024)
            total_size += file_size
            print(f"  {idx:2d}. {Path(file).name} ({file_size:.1f} MB)")
        print(f"\n  总大小: {total_size:.1f} MB")
    
    print("\n" + "=" * 70)
    print(" " * 15 + "感谢使用三角洲击杀剪辑工具！")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断程序")
    except Exception as e:
        print(f"\n\n✗ 程序异常: {e}")
        import traceback
        traceback.print_exc()