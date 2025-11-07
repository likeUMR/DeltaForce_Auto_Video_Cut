###三角洲视频剪辑V0.1
```
code/
├── clipper.py     #视频剪辑模块
├── config.py      #配置文件（更改分辨率、ROI、阈值设定等）
├── detector.py    #击杀检测模块
├── main.py        #主程序入口（设置文件地址）
├── __pycache__
└──ffmpeg/bin
   ├──ffmpeg.exe
   ├──ffplay.exe
   └──ffprobe.exe
match_templates/
├── game_events/          # 游戏事件（击杀、击倒提示）
└── ui_elements/          # 界面元素（搜索UI）
output/
test
   └──test_img
   └──test_video.mp4
README.md
requirements.txt
``` 
1.按照requirements.txt配置环境就可以
2.正式运行：
""
python main.py
""
程序会：
检查环境（FFmpeg、视频、模板）
加载模板
检测击杀（显示进度）
合并重复检测
剪辑视频片段
3.配置说明
（1）视频参数
VIDEO_WIDTH = 2304   # 你的游戏分辨率宽度
VIDEO_HEIGHT = 1440  # 你的游戏分辨率高度
（2）ROI 参数（击杀图标检测区域）
# 根据 auto_roi_detector 的检测结果：
# 击杀图标位于 (1136, 1013) 附近

ROI_PERCENT = 0.15   # ROI占屏幕的15%
ROI_X = 980          # ROI左上角X坐标
ROI_Y = 925          # ROI左上角Y坐标
ROI_WIDTH = 345      # ROI宽度
ROI_HEIGHT = 216     # ROI高度
（3）检测参数
SAMPLE_FPS = 5           # 每秒检测5帧（提高=更精确但更慢）
MATCH_THRESHOLD = 0.70   # 匹配阈值（0.6-0.8，越高越严格）
（4）剪辑参数
CLIP_BEFORE = 3.0  # 击杀前保留3秒
CLIP_AFTER = 2.0   # 击杀后保留2秒
TIME_WINDOW = 1.0  # 1秒内的检测合并为一个事件
4.ffmpeg需要自己添加（这里我没有上传到git）
5.完整项目（包含数据）网盘链接
通过网盘分享的文件：Delto
链接: https://pan.baidu.com/s/1CofqU5x-QDQo5N6HEW58KQ 提取码: b4pe 
--来自百度网盘超级会员v1的分享