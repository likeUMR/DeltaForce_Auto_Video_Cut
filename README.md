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
# 使用说明

## 1. 环境配置

按照 `requirements.txt` 安装环境即可：

```
pip install -r requirements.txt
```

---

## 2. 运行方式

### 🖥️ 图形化界面（UI）

运行主程序：

```
python main.py
```

**UI 功能包括：**

* 拖放或选择多个视频文件
* 自动显示视频信息（时长、分辨率、大小）
* 批量处理视频（自动跳过已处理部分）
* 实时显示处理进度
* 处理完成后自动保存（文件名前缀：`[一杀一剪]`）

---

### 🛠️ 命令行版本

```
python code/main.py
```

程序将自动执行以下步骤：

1. 检查运行环境（FFmpeg、视频文件、模板）
2. 加载模板
3. 检测击杀事件（显示实时进度）
4. 合并重复检测结果
5. 自动剪辑输出片段

---

## 3. 配置说明

### （1）视频参数

```python
VIDEO_WIDTH = 2304   # 游戏分辨率宽
VIDEO_HEIGHT = 1440  # 游戏分辨率高
```

### （2）ROI 参数（击杀图标检测区域）

```python
ROI_X = 980          # ROI 左上角 X 坐标
ROI_Y = 925          # ROI 左上角 Y 坐标
ROI_WIDTH = 345      # ROI 宽度
ROI_HEIGHT = 216     # ROI 高度
```

### （3）检测参数

```python
SAMPLE_FPS = 5           # 每秒检测帧数（越高越精确但越慢）
MATCH_THRESHOLD = 0.70   # 匹配阈值（推荐：0.6–0.8）
```

### （4）剪辑参数

```python
CLIP_BEFORE = 3.0  # 击杀前保留秒数
CLIP_AFTER = 2.0   # 击杀后保留秒数
TIME_WINDOW = 3.0  # 时间窗口内事件合并（秒）
```

---

## 4. FFmpeg

程序需要本地安装 FFmpeg（项目未自带，请自行添加到系统路径）

---

---

## 5. 构建方式

运行构建脚本生成可执行文件：
```
build_release.bat
```

---

## 6. 完整项目（含数据）

**百度网盘下载链接：**

```
链接：https://pan.baidu.com/s/1CofqU5x-QDQo5N6HEW58KQ
提取码：b4pe
```
