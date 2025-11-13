"""
启动UI界面的入口文件
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径，以便导入模块
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication

# 直接使用绝对导入，避免相对导入问题
from UI_interface.main_window import MainWindow


def main():
    try:
        print("[DEBUG] 初始化QApplication")
        app = QApplication(sys.argv)
        
        # 设置应用样式
        app.setStyle('Fusion')
        print("[DEBUG] 创建MainWindow")
        
        window = MainWindow()
        print("[DEBUG] 显示窗口")
        window.show()
        
        print("[DEBUG] 进入事件循环")
        sys.exit(app.exec())
    except Exception as e:
        print(f"[ERROR] 程序启动时发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
        sys.exit(1)


if __name__ == '__main__':
    main()

