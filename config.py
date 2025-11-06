"""
三角洲游戏配置文件
基于自动检测结果生成
"""

class Config:
    # 视频参数（三角洲游戏）
    VIDEO_WIDTH = 2304
    VIDEO_HEIGHT = 1440
    
    # ROI参数 - 击杀图标检测区域
    # 根据检测结果：击杀图标位于 (1136, 1013) 附近
    # 图标大小约 32x40 或 45x27
    # 建议ROI区域覆盖屏幕下方中央区域
    
    # 方案1：以检测到的位置为中心，设置较大的ROI（推荐）
    # ROI_PERCENT = 0.15  # ROI占画面的15%
    # ROI_WIDTH = int(VIDEO_WIDTH * ROI_PERCENT)  # 约 345
    # ROI_HEIGHT = int(VIDEO_HEIGHT * ROI_PERCENT)  # 约 216
    
    # # ROI位置：以击杀图标中心 (1152, 1033) 为中心
    # KILL_ICON_CENTER_X = 1152
    # KILL_ICON_CENTER_Y = 1033
    # ROI_X = KILL_ICON_CENTER_X - ROI_WIDTH // 2  # 约 980
    # ROI_Y = KILL_ICON_CENTER_Y - ROI_HEIGHT // 2  # 约 925
    
    # 方案2：如果方案1效果不好，可以使用固定位置
    ROI_X = 950  # 屏幕下方中央
    ROI_Y = 900
    ROI_WIDTH = 400
    ROI_HEIGHT = 250
    
    # 检测参数
    SAMPLE_FPS = 10  # 抽帧频率（每秒检测5帧）
    MATCH_THRESHOLD = 0.9  # 模板匹配阈值（从0.999的结果看，可以设置较高）
    
    # 模板文件配置
    TEMPLATE_DIR = r"C:\Users\admin\Desktop\Delto\match_templates\game_events"
    
    # 三角洲游戏的击杀图标模板
    # 根据你的模板文件，包含多种击杀类型
    TEMPLATE_NAMES = [
        "elimination.png",           # 普通击杀
        "elimination_headshot.png",  # 爆头击杀
        
        # 如果有其他模板，继续添加
    ]
    
    # 时间窗口参数
    TIME_WINDOW = 3.0  # 1秒内算同一个击杀事件
    CLIP_BEFORE = 2.0  # 击杀前保留3秒（可以看到击杀过程）
    CLIP_AFTER = 2.0   # 击杀后保留2秒（可以看到击杀确认）
    
    # 输出参数
    OUTPUT_VIDEO_CODEC = "libx264"  # H.264编码
    OUTPUT_CRF = 18  # 质量参数（18=高质量，23=标准）
    OUTPUT_PRESET = "fast"  # 编码速度（fast=较快，medium=平衡）