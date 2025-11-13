import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt6.QtGui import QFont, QColor, QPainter, QPixmap, QDragEnterEvent, QDropEvent
import os

# 使用绝对导入
from UI_interface.banner_widget import BannerWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.banner_list = []
        self.processing_queue = []
        self.is_processing = False
        self.current_processing_index = -1
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('三角洲自动剪辑软件')
        self.setGeometry(100, 100, 1200, 800)
        
        # 主容器
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, stretch=0)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, stretch=1)
        
        # 启用拖放
        self.setAcceptDrops(True)
        
    def create_left_panel(self):
        """创建左侧面板"""
        left_widget = QWidget()
        left_widget.setFixedWidth(250)
        left_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-right: 1px solid #e0e0e0;
            }
        """)
        
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(20)
        
        # 标题
        title_label = QLabel('三角洲<br>自动剪辑软件')
        title_label.setFont(QFont('Microsoft YaHei', 18, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #202124;
                padding: 10px;
            }
        """)
        left_layout.addWidget(title_label)
        
        # 添加弹性空间
        left_layout.addStretch()
        
        # 按钮组
        button_layout = QVBoxLayout()
        button_layout.setSpacing(12)
        
        # 设置按钮
        settings_btn = QPushButton('设置')
        settings_btn.setFixedHeight(45)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #202124;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #c4c7c5;
            }
            QPushButton:pressed {
                background-color: #e8eaed;
            }
        """)
        settings_btn.clicked.connect(self.on_settings_clicked)
        button_layout.addWidget(settings_btn)
        
        # 打断按钮
        interrupt_btn = QPushButton('打断')
        interrupt_btn.setFixedHeight(45)
        interrupt_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #202124;
                border: 1px solid #dadce0;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #c4c7c5;
            }
            QPushButton:pressed {
                background-color: #e8eaed;
            }
        """)
        interrupt_btn.clicked.connect(self.on_interrupt_clicked)
        button_layout.addWidget(interrupt_btn)
        
        # 启动按钮
        start_btn = QPushButton('启动')
        start_btn.setFixedHeight(45)
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #34a853;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2d8f47;
            }
            QPushButton:pressed {
                background-color: #267d3e;
            }
        """)
        start_btn.clicked.connect(self.on_start_clicked)
        button_layout.addWidget(start_btn)
        
        left_layout.addLayout(button_layout)
        
        return left_widget
        
    def create_right_panel(self):
        """创建右侧面板"""
        right_widget = QWidget()
        right_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(0)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #f1f3f4;
                width: 12px;
                border: none;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #dadce0;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #bdc1c6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        right_layout.addWidget(scroll_area)
        
        # 保存引用
        self.scroll_area = scroll_area
        self.content_widget = content_widget
        self.content_layout = content_layout
        
        # 创建默认空白Banner
        self.add_empty_banner()
        
        return right_widget
        
    def add_empty_banner(self):
        """添加空白Banner"""
        banner = BannerWidget(is_empty=True, index=len(self.banner_list) + 1)
        banner.file_selected.connect(self.on_file_selected)
        banner.delete_requested.connect(self.on_banner_deleted)
        
        # 插入到倒数第二个位置（在stretch之前）
        self.content_layout.insertWidget(self.content_layout.count() - 1, banner)
        self.banner_list.append(banner)
        
        # 更新所有Banner的序号
        self.update_banner_indices()
        
    def add_video_banner(self, video_path):
        """添加视频Banner"""
        banner = BannerWidget(is_empty=False, index=len(self.banner_list) + 1)
        banner.set_video_info(video_path)
        banner.delete_requested.connect(self.on_banner_deleted)
        
        # 插入到倒数第二个位置（在stretch之前）
        self.content_layout.insertWidget(self.content_layout.count() - 1, banner)
        self.banner_list.append(banner)
        
        # 更新所有Banner的序号
        self.update_banner_indices()
        
    def update_banner_indices(self):
        """更新所有Banner的序号"""
        for i, banner in enumerate(self.banner_list):
            banner.set_index(i + 1)
            
    def on_file_selected(self, banner_widget, file_paths):
        """处理文件选择"""
        # 移除空白Banner
        if banner_widget in self.banner_list:
            self.banner_list.remove(banner_widget)
            self.content_layout.removeWidget(banner_widget)
            banner_widget.deleteLater()
        
        # 为每个文件创建Banner
        for file_path in file_paths:
            self.add_video_banner(file_path)
        
        # 添加新的空白Banner
        self.add_empty_banner()
        
    def on_banner_deleted(self, banner_widget):
        """处理Banner删除"""
        if banner_widget in self.banner_list:
            self.banner_list.remove(banner_widget)
            self.content_layout.removeWidget(banner_widget)
            banner_widget.deleteLater()
            self.update_banner_indices()
            
        # 如果没有Banner了，添加一个空白Banner
        if len(self.banner_list) == 0:
            self.add_empty_banner()
            
    def on_settings_clicked(self):
        """设置按钮点击"""
        QMessageBox.information(self, '提示', '设置功能暂未实现')
        
    def on_interrupt_clicked(self):
        """打断按钮点击"""
        if self.is_processing:
            self.is_processing = False
            self.current_processing_index = -1
            # 重置所有Banner状态
            for banner in self.banner_list:
                banner.reset_status()
            QMessageBox.information(self, '提示', '已打断处理')
        else:
            QMessageBox.information(self, '提示', '当前没有正在处理的任务')
            
    def on_start_clicked(self):
        """启动按钮点击"""
        try:
            print("[DEBUG] 启动按钮被点击")
            # 收集所有有视频且未完成的Banner
            video_banners = [
                banner for banner in self.banner_list 
                if not banner.is_empty and banner.status != 'completed'
            ]
            print(f"[DEBUG] 找到 {len(video_banners)} 个未完成的视频Banner")
            
            # 统计已完成的Banner数量
            completed_count = len([
                banner for banner in self.banner_list 
                if not banner.is_empty and banner.status == 'completed'
            ])
            
            if len(video_banners) == 0:
                if completed_count > 0:
                    QMessageBox.information(self, '提示', f'所有视频已完成处理（共{completed_count}个），没有需要处理的视频')
                else:
                    QMessageBox.warning(self, '警告', '请先添加视频文件')
                return
                
            if self.is_processing:
                QMessageBox.warning(self, '警告', '已有任务正在处理中')
                return
            
            # 显示跳过信息
            if completed_count > 0:
                print(f"[DEBUG] 跳过 {completed_count} 个已完成的Banner")
            
            self.processing_queue = video_banners
            self.is_processing = True
            self.current_processing_index = 0
            
            # 更新状态
            for i, banner in enumerate(self.processing_queue):
                if i == 0:
                    print(f"[DEBUG] 设置Banner {i+1} 为处理中状态")
                    banner.set_status('processing')
                else:
                    print(f"[DEBUG] 设置Banner {i+1} 为等待状态")
                    banner.set_status('waiting')
            
            # 开始处理第一个
            print("[DEBUG] 开始处理第一个视频")
            self.process_next_video()
        except Exception as e:
            print(f"[ERROR] 启动处理时发生错误: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'启动处理时发生错误:\n{str(e)}')
        
    def process_next_video(self):
        """处理下一个视频"""
        try:
            print(f"[DEBUG] process_next_video: is_processing={self.is_processing}, index={self.current_processing_index}, queue_len={len(self.processing_queue)}")
            if not self.is_processing or self.current_processing_index >= len(self.processing_queue):
                print("[DEBUG] 处理完成或已停止")
                self.is_processing = False
                self.current_processing_index = -1
                return
                
            current_banner = self.processing_queue[self.current_processing_index]
            print(f"[DEBUG] 开始处理视频 {self.current_processing_index + 1}/{len(self.processing_queue)}")
            
            # 开始进度动画
            print("[DEBUG] 启动进度动画")
            current_banner.start_progress_animation()
            print("[DEBUG] 进度动画已启动")
            
            # 5秒后完成
            print("[DEBUG] 设置5秒后完成的定时器")
            QTimer.singleShot(5000, lambda banner=current_banner: self.on_video_processed(banner))
            print("[DEBUG] 定时器已设置")
        except Exception as e:
            print(f"[ERROR] process_next_video 发生错误: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'处理视频时发生错误:\n{str(e)}')
        
    def on_video_processed(self, banner):
        """视频处理完成"""
        try:
            print(f"[DEBUG] on_video_processed: is_processing={self.is_processing}")
            if not self.is_processing:
                print("[DEBUG] 处理已停止，忽略完成回调")
                return
                
            print("[DEBUG] 完成当前视频处理")
            banner.complete_processing()
            
            # 处理下一个
            self.current_processing_index += 1
            
            # 更新状态
            if self.current_processing_index < len(self.processing_queue):
                print(f"[DEBUG] 继续处理下一个视频 {self.current_processing_index + 1}")
                self.processing_queue[self.current_processing_index].set_status('processing')
                self.process_next_video()
            else:
                # 所有视频处理完成
                print("[DEBUG] 所有视频处理完成")
                self.is_processing = False
                self.current_processing_index = -1
        except Exception as e:
            print(f"[ERROR] on_video_processed 发生错误: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, '错误', f'完成处理时发生错误:\n{str(e)}')
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                # 检查是否是视频文件
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v']:
                    files.append(file_path)
        
        if files:
            # 找到空白Banner
            empty_banners = [banner for banner in self.banner_list if banner.is_empty]
            if empty_banners:
                self.on_file_selected(empty_banners[0], files)
            else:
                # 如果没有空白Banner，先添加视频Banner
                for file_path in files:
                    self.add_video_banner(file_path)
                self.add_empty_banner()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

