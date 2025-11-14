"""
三角洲自动剪辑软件 - 主入口文件
启动UI界面程序
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径，确保可以导入UI_interface模块
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 导入并调用UI入口
from UI_interface.run_ui import main

if __name__ == '__main__':
    main()

