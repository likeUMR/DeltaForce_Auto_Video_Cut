###三角洲视频剪辑V0.1
```
code/
├── clipper.py     #视频剪辑模块
├── config.py      #配置文件（更改分辨率、ROI、阈值设定等）
├── detector.py    #击杀检测模块
└── main.py        #命令行版本入口
UI_interface/
├── main_window.py      #主窗口
├── banner_widget.py   #视频Banner组件
├── video_processor.py #视频处理逻辑
├── video_worker.py    #后台处理线程
├── video_thumbnail.py #缩略图提取
└── run_ui.py          #UI入口
match_templates/
├── game_events/          # 游戏事件（击杀、击倒提示）
└── ui_elements/          # 界面元素（搜索UI）
main.py                   #主入口（启动UI界面）
requirements.txt
``` 
1.按照requirements.txt配置环境就可以
2.正式运行：
""
python main.py
""
UI界面功能：
拖放或选择多个视频文件
自动显示视频信息（时长、分辨率、大小）
批量处理视频（自动跳过已处理）
实时显示处理进度
处理完成后自动保存（文件名前缀：[一杀一剪]）
命令行版本：
""
python code/main.py
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
TIME_WINDOW = 3.0  # 3秒内的检测合并为一个事件
4.ffmpeg需要自己添加（这里我没有上传到git）
5.完整项目（包含数据）网盘链接
通过网盘分享的文件：Delto
链接: https://pan.baidu.com/s/1CofqU5x-QDQo5N6HEW58KQ 提取码: b4pe 
--来自百度网盘超级会员v1的分享