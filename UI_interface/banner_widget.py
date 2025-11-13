from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QPoint, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPixmap, QFont, QIcon, QPolygon, QImage
import os

# 导入视频缩略图提取模块（使用FFmpeg）
try:
    from UI_interface.video_thumbnail import extract_first_frame_to_file
except ImportError:
    try:
        from .video_thumbnail import extract_first_frame_to_file
    except ImportError:
        def extract_first_frame_to_file(*args, **kwargs):
            print(f"[WARNING] 视频缩略图模块未找到")
            return None

# 导入视频保存模块
try:
    from UI_interface.video_saver import save_video_with_prefix
except ImportError:
    # 如果导入失败，尝试相对导入
    try:
        from .video_saver import save_video_with_prefix
    except ImportError:
        # 如果都失败，定义一个占位函数
        def save_video_with_prefix(input_path: str, prefix: str = "[一杀一剪]") -> str:
            print(f"[WARNING] 视频保存模块未找到，使用占位函数")
            return None


class BannerWidget(QWidget):
    """Banner组件"""
    file_selected = pyqtSignal(object, list)  # banner_widget, file_paths
    delete_requested = pyqtSignal(object)  # banner_widget
    
    def __init__(self, is_empty=False, index=1):
        super().__init__()
        self.is_empty = is_empty
        self.index = index
        self.video_path = None
        self.video_name = None
        self.video_duration = None
        self.video_resolution = None
        self.video_size = 0  # 视频文件大小（字节）
        
        # 存储原始视频信息（用于处理完成后对比显示）
        self.original_duration = None  # 原始时长字符串
        self.original_duration_seconds = 0.0  # 原始时长（秒）
        self.original_size = 0  # 原始文件大小（字节）
        self.status = 'idle'  # idle, waiting, processing, completed
        self._progress = 0.0  # 使用私有变量存储实际值
        self.output_path = None
        
        self.progress_animation = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setFixedHeight(120)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # 序号标签
        index_label = QLabel(str(self.index))
        index_label.setFixedWidth(30)
        index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        index_label.setFont(QFont('Microsoft YaHei', 12, QFont.Weight.Bold))
        index_label.setStyleSheet("""
            QLabel {
                color: #5f6368;
                background-color: transparent;
                border-radius: 4px;
            }
        """)
        layout.addWidget(index_label)
        self.index_label = index_label
        
        # 图片区域
        image_label = QLabel()
        image_label.setFixedSize(160, 96)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("""
            QLabel {
                background-color: #f1f3f4;
                border-radius: 4px;
            }
        """)
        
        if self.is_empty:
            # 空白Banner显示灰色
            pixmap = QPixmap(160, 96)
            pixmap.fill(QColor(241, 243, 244))
            image_label.setPixmap(pixmap)
        else:
            image_label.setText('加载中...')
            
        layout.addWidget(image_label)
        self.image_label = image_label
        
        # 右侧信息区域
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)
        
        # 第一行：视频名称
        name_label = QLabel()
        name_label.setFont(QFont('Microsoft YaHei', 14, QFont.Weight.Medium))
        name_label.setStyleSheet("""
            QLabel {
                color: #202124;
                background-color: transparent;
            }
        """)
        if self.is_empty:
            name_label.setText('拖入视频或选择视频')
        info_layout.addWidget(name_label)
        self.name_label = name_label
        
        # 第二行：时长和分辨率
        info_label = QLabel()
        info_label.setFont(QFont('Microsoft YaHei', 12))
        info_label.setStyleSheet("""
            QLabel {
                color: #5f6368;
                background-color: transparent;
            }
        """)
        info_label.setTextFormat(Qt.TextFormat.RichText)  # 启用富文本格式
        if not self.is_empty:
            info_label.setText('')
        info_layout.addWidget(info_label)
        self.info_label = info_label
        
        # 第三行：路径或文件选择
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(8)
        
        if self.is_empty:
            # 文件选择按钮
            select_btn = QPushButton('选择文件')
            select_btn.setFixedHeight(32)
            select_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #1a73e8;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    font-size: 12px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background-color: #f8f9fa;
                    border-color: #c4c7c5;
                }
                QPushButton:pressed {
                    background-color: #e8eaed;
                }
            """)
            select_btn.clicked.connect(self.on_select_file)
            path_layout.addWidget(select_btn)
            self.select_btn = select_btn
            self.path_label = None
        else:
            # 路径标签
            path_label = QLabel()
            path_label.setFont(QFont('Microsoft YaHei', 11))
            path_label.setStyleSheet("""
                QLabel {
                    color: #5f6368;
                    background-color: transparent;
                }
            """)
            path_label.setWordWrap(True)
            path_layout.addWidget(path_label)
            self.path_label = path_label
            self.select_btn = None
            
        info_layout.addLayout(path_layout)
        
        # 添加弹性空间
        info_layout.addStretch()
        
        layout.addLayout(info_layout, stretch=1)
        
        # 删除按钮
        delete_btn = QPushButton('×')
        delete_btn.setFixedSize(32, 32)
        delete_btn.setFont(QFont('Microsoft YaHei', 20))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #5f6368;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: #f1f3f4;
                color: #202124;
            }
            QPushButton:pressed {
                background-color: #e8eaed;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        layout.addWidget(delete_btn)
        
    def set_index(self, index):
        """设置序号"""
        self.index = index
        self.index_label.setText(str(index))
        self.update_index_label_style()
    
    def update_index_label_style(self):
        """更新序号标签样式（根据状态）"""
        if self.status == 'completed':
            # 完成状态：浅绿色背景，深色文字
            self.index_label.setStyleSheet("""
                QLabel {
                    color: #202124;
                    background-color: #c8e6c9;
                    border-radius: 4px;
                }
            """)
        else:
            # 其他状态：默认样式
            self.index_label.setStyleSheet("""
                QLabel {
                    color: #5f6368;
                    background-color: transparent;
                    border-radius: 4px;
                }
            """)
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        
    def set_video_info(self, video_path, video_info=None):
        """设置视频信息"""
        self.is_empty = False
        self.video_path = video_path
        
        # 提取文件名
        self.video_name = os.path.basename(video_path)
        self.name_label.setText(self.video_name)
        
        # 显示路径
        if self.path_label:
            self.path_label.setText(video_path)
        else:
            # 如果之前是空白Banner，需要替换选择按钮
            if self.select_btn:
                self.select_btn.hide()
                path_label = QLabel()
                path_label.setFont(QFont('Microsoft YaHei', 11))
                path_label.setStyleSheet("""
                    QLabel {
                        color: #5f6368;
                        background-color: transparent;
                    }
                """)
                path_label.setWordWrap(True)
                path_label.setText(video_path)
                self.select_btn.parent().layout().addWidget(path_label)
                self.path_label = path_label
                self.select_btn = None
        
        # 获取视频文件大小
        video_size = 0
        if os.path.exists(video_path):
            try:
                video_size = os.path.getsize(video_path)
            except Exception as e:
                print(f"[WARNING] 无法获取视频文件大小: {e}")
        
        # 使用传入的视频信息，如果没有则使用默认值
        if video_info:
            self.video_duration = video_info.get('duration_str', '00:00:00')
            self.video_resolution = f"{video_info.get('width', 0)}x{video_info.get('height', 0)}"
            
            # 存储原始信息
            self.original_duration = self.video_duration
            self.original_duration_seconds = video_info.get('duration', 0.0)
        else:
            # 默认值
            self.video_duration = '00:00:00'
            self.video_resolution = '0x0'
        
        self.video_size = video_size
        
        # 存储原始大小
        self.original_size = video_size
        
        # 显示：时长 | 分辨率 | 文件大小
        size_str = self.format_file_size(video_size)
        self.info_label.setText(f'{self.video_duration} | {self.video_resolution} | {size_str}')
        self.info_label.show()
        self.update_index_label_style()  # 更新序号标签样式
        
        # 加载封面图（这里用占位图）
        self.load_thumbnail()
        
    def load_thumbnail(self):
        """加载视频封面图（使用FFmpeg提取首帧）"""
        if not self.video_path or not os.path.exists(self.video_path):
            # 如果没有视频路径或文件不存在，使用占位图
            pixmap = QPixmap(160, 96)
            pixmap.fill(QColor(200, 200, 200))
            self.image_label.setPixmap(pixmap)
            return
        
        try:
            # 使用FFmpeg提取视频首帧到临时文件
            temp_file = extract_first_frame_to_file(
                self.video_path,
                output_width=160,
                output_height=96
            )
            
            if temp_file and os.path.exists(temp_file):
                # 加载PNG图像
                pixmap = QPixmap(temp_file)
                if not pixmap.isNull():
                    self.image_label.setPixmap(pixmap)
                    print(f"[DEBUG] 成功加载视频首帧: {self.video_path}")
                else:
                    print(f"[WARNING] 无法加载提取的首帧图像: {self.video_path}")
                    pixmap = QPixmap(160, 96)
                    pixmap.fill(QColor(200, 200, 200))
                    self.image_label.setPixmap(pixmap)
                
                # 清理临时文件
                try:
                    os.remove(temp_file)
                except:
                    pass
            else:
                print(f"[WARNING] 无法提取视频首帧: {self.video_path}")
                pixmap = QPixmap(160, 96)
                pixmap.fill(QColor(200, 200, 200))
                self.image_label.setPixmap(pixmap)
        except Exception as e:
            print(f"[ERROR] 加载视频首帧时发生错误: {e}")
            import traceback
            traceback.print_exc()
            # 使用占位图
            pixmap = QPixmap(160, 96)
            pixmap.fill(QColor(200, 200, 200))
            self.image_label.setPixmap(pixmap)
        
    def on_select_file(self):
        """选择文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            '选择视频文件',
            '',
            '视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.m4v);;所有文件 (*.*)'
        )
        
        if files:
            self.file_selected.emit(self, files)
            
    def set_status(self, status):
        """设置状态"""
        self.status = status
        self.update_index_label_style()  # 更新序号标签样式
        self.update()
        
    def start_progress_animation(self):
        """开始进度动画（已废弃，现在使用真实进度更新）"""
        # 这个方法保留用于兼容，但不再使用固定5秒动画
        # 真实进度通过set_progress方法更新
        self.status = 'processing'
        self._progress = 0.0
        self.update()
        
    def complete_processing(self, output_file=None):
        """完成处理"""
        self.status = 'completed'
        self._progress = 1.0
        
        # 使用处理后的输出文件路径
        if output_file and os.path.exists(output_file):
            self.output_path = output_file
            print(f"[DEBUG] 处理完成，输出文件: {self.output_path}")
        else:
            # 如果没有输出文件，使用原来的保存逻辑（添加前缀）
            if self.video_path:
                print(f"[DEBUG] 开始保存视频: {self.video_path}")
                self.output_path = save_video_with_prefix(self.video_path, prefix="[一杀一剪]")
            else:
                self.output_path = None
        
        if self.output_path:
            # 获取输出文件信息（时长和大小）
            output_size = 0
            output_duration_str = None
            output_duration_seconds = 0.0
            
            if os.path.exists(self.output_path):
                try:
                    # 获取文件大小
                    output_size = os.path.getsize(self.output_path)
                    
                    # 获取视频时长（需要从VideoProcessor获取）
                    # 这里我们需要从外部传入，或者在这里重新获取
                    # 为了简化，我们先尝试从processor获取，如果没有则使用原始时长
                    from UI_interface.video_processor import VideoProcessor
                    processor = VideoProcessor()
                    try:
                        output_info = processor.get_video_info(self.output_path)
                        output_duration_seconds = output_info.get('duration', 0.0)
                        output_duration_str = output_info.get('duration_str', '00:00:00')
                    except Exception as e:
                        print(f"[WARNING] 无法获取输出视频时长: {e}")
                        output_duration_str = self.video_duration
                        output_duration_seconds = self.original_duration_seconds
                        
                except Exception as e:
                    print(f"[WARNING] 无法获取输出文件大小: {e}")
            
            # 更新第二行显示：原始时长（划掉） 新时长（绿色） | 分辨率 | 原始大小（划掉） 新大小（绿色）
            if output_size > 0 and output_duration_str:
                # 格式化时长和大小
                new_size_str = self.format_file_size(output_size)
                original_size_str = self.format_file_size(self.original_size) if hasattr(self, 'original_size') else self.format_file_size(self.video_size)
                original_duration = self.original_duration if hasattr(self, 'original_duration') else self.video_duration
                
                # 使用HTML格式：删除线 + 绿色新值
                self.info_label.setText(
                    f'<s style="color: #9aa0a6;">{original_duration}</s> '
                    f'<span style="color: #34a853;">{output_duration_str}</span> | '
                    f'{self.video_resolution} | '
                    f'<s style="color: #9aa0a6;">{original_size_str}</s> '
                    f'<span style="color: #34a853;">{new_size_str}</span>'
                )
            else:
                # 如果无法获取新信息，保持原显示
                size_str = self.format_file_size(self.video_size) if hasattr(self, 'video_size') else '0 B'
                self.info_label.setText(
                    f'{self.video_duration} | {self.video_resolution} | {size_str}'
                )
            
            # 更新序号标签样式为绿色
            self.update_index_label_style()
            
            if self.path_label:
                self.path_label.setText(f'已保存到：{self.output_path}')
                self.path_label.setStyleSheet("""
                    QLabel {
                        color: #34a853;
                        background-color: transparent;
                    }
                """)
            print(f"[DEBUG] 视频处理成功: {self.output_path}")
        else:
            # 处理失败，显示错误信息
            if self.path_label:
                self.path_label.setText(f'处理失败：{self.video_path}')
                self.path_label.setStyleSheet("""
                    QLabel {
                        color: #ea4335;
                        background-color: transparent;
                    }
                """)
            print(f"[ERROR] 视频处理失败: {self.video_path}")
        
        if self.progress_animation:
            self.progress_animation.stop()
            
        self.update()
        
    def reset_status(self):
        """重置状态（包括完成状态）"""
        self.status = 'idle'
        self._progress = 0.0
        self.output_path = None  # 清除输出路径
        
        if self.progress_animation:
            self.progress_animation.stop()
        
        # 恢复原始文件大小显示（不使用绿色）
        if hasattr(self, 'video_size') and self.video_size > 0:
            size_str = self.format_file_size(self.video_size)
            if hasattr(self, 'video_duration') and hasattr(self, 'video_resolution'):
                self.info_label.setText(f'{self.video_duration} | {self.video_resolution} | {size_str}')
        
        # 恢复序号标签样式
        self.update_index_label_style()
            
        if self.path_label and self.video_path:
            self.path_label.setText(self.video_path)
            self.path_label.setStyleSheet("""
                QLabel {
                    color: #5f6368;
                    background-color: transparent;
                }
            """)
            
        self.update()
        
    def get_progress(self):
        """获取进度值"""
        return self._progress
        
    def set_progress(self, value):
        """设置进度值"""
        try:
            if self._progress != value:
                self._progress = value
                self.update()
        except Exception as e:
            print(f"[ERROR] set_progress 发生错误: {e}")
            import traceback
            traceback.print_exc()
            raise
        
    progress = pyqtProperty(float, get_progress, set_progress)
        
    def paintEvent(self, event):
        """绘制事件"""
        try:
            super().paintEvent(event)
            
            # 只在需要绘制时创建 QPainter
            need_draw_progress = self.status == 'processing' and self.progress > 0
            need_draw_icon = self.status in ['processing', 'waiting']
            
            if need_draw_progress or need_draw_icon:
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                rect = self.rect()
                
                # 绘制进度条背景
                if need_draw_progress:
                    # 绿色进度条
                    progress_color = QColor(52, 168, 83, 180)  # 半透明绿色
                    painter.setBrush(progress_color)
                    painter.setPen(Qt.PenStyle.NoPen)
                    
                    progress_width = int(rect.width() * self.progress)
                    progress_rect = QRect(0, 0, progress_width, rect.height())
                    painter.drawRoundedRect(progress_rect, 8, 8)
                
                # 绘制状态图标
                if need_draw_icon:
                    icon_size = 32
                    icon_x = rect.width() - icon_size - 20
                    icon_y = rect.height() - icon_size - 12
                    
                    if self.status == 'processing':
                        # 播放图标（简单的三角形）
                        painter.setBrush(QColor(255, 255, 255, 200))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawEllipse(icon_x, icon_y, icon_size, icon_size)
                        
                        painter.setBrush(QColor(52, 168, 83))
                        painter.setPen(Qt.PenStyle.NoPen)
                        # 绘制三角形
                        triangle_points = [
                            QPoint(icon_x + icon_size // 2 - 6, icon_y + icon_size // 2 - 8),
                            QPoint(icon_x + icon_size // 2 - 6, icon_y + icon_size // 2 + 8),
                            QPoint(icon_x + icon_size // 2 + 8, icon_y + icon_size // 2)
                        ]
                        polygon = QPolygon(triangle_points)
                        painter.drawPolygon(polygon)
                        
                    elif self.status == 'waiting':
                        # 等待图标（三个点）
                        painter.setBrush(QColor(255, 255, 255, 200))
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawEllipse(icon_x, icon_y, icon_size, icon_size)
                        
                        painter.setBrush(QColor(95, 99, 104))
                        painter.setPen(Qt.PenStyle.NoPen)
                        dot_size = 6
                        dot_y = icon_y + icon_size // 2
                        for i, dot_x in enumerate([icon_x + icon_size // 2 - 8, icon_x + icon_size // 2, icon_x + icon_size // 2 + 8]):
                            painter.drawEllipse(dot_x - dot_size // 2, dot_y - dot_size // 2, dot_size, dot_size)
                
                # QPainter 会在离开作用域时自动结束
                painter.end()
        except Exception as e:
            print(f"[ERROR] paintEvent 发生错误: {e}")
            import traceback
            traceback.print_exc()

