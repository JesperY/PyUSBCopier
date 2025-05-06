from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QListWidget, QListWidgetItem, QFileDialog,
                            QGridLayout, QMessageBox, QFrame, QGroupBox,
                            QInputDialog, QScrollArea)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from ..core.config import config
from .icons import get_icon

class ConfigEditorGUI(QMainWindow):
    """配置编辑器界面"""
    def __init__(self):
        super().__init__()
        
        # 设置窗口图标
        self.setWindowIcon(get_icon())
        
        # 初始化UI
        self.initUI()
        
    def initUI(self):
        """初始化用户界面"""
        # 设置窗口基本属性
        self.setWindowTitle('配置编辑器')
        self.setGeometry(300, 300, 700, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签提示
        title_label = QLabel('编辑配置文件')
        title_label.setFont(QFont('SansSerif', 14))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建滚动区域以容纳所有内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll.setWidget(scroll_content)
        
        # 基本设置组
        basic_group = QGroupBox("基本设置")
        basic_layout = QGridLayout(basic_group)
        
        # 备份目标路径
        backup_label = QLabel('备份目标路径:')
        self.backup_path_edit = QLineEdit(config.backup_dst)
        browse_button = QPushButton('浏览...')
        browse_button.clicked.connect(self.browse_backup_dir)
        
        basic_layout.addWidget(backup_label, 0, 0)
        basic_layout.addWidget(self.backup_path_edit, 0, 1)
        basic_layout.addWidget(browse_button, 0, 2)
        
        scroll_layout.addWidget(basic_group)
        
        # 添加分割线
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        scroll_layout.addWidget(separator1)
        
        # 目录名白名单组
        dirname_group = QGroupBox("目录名白名单")
        dirname_layout = QVBoxLayout(dirname_group)
        
        self.dirname_list = QListWidget()
        self.dirname_list.setMaximumHeight(120)
        self.load_list_items(self.dirname_list, config.white_list.get('dirname', []))
        
        dirname_buttons_layout = QHBoxLayout()
        add_dirname_btn = QPushButton('添加')
        add_dirname_btn.clicked.connect(lambda: self.add_list_item(self.dirname_list, '目录名'))
        remove_dirname_btn = QPushButton('删除')
        remove_dirname_btn.clicked.connect(lambda: self.remove_list_item(self.dirname_list))
        
        dirname_buttons_layout.addWidget(add_dirname_btn)
        dirname_buttons_layout.addWidget(remove_dirname_btn)
        
        dirname_layout.addWidget(self.dirname_list)
        dirname_layout.addLayout(dirname_buttons_layout)
        
        scroll_layout.addWidget(dirname_group)
        
        # 文件名白名单组
        filename_group = QGroupBox("文件名白名单")
        filename_layout = QVBoxLayout(filename_group)
        
        self.filename_list = QListWidget()
        self.filename_list.setMaximumHeight(120)
        self.load_list_items(self.filename_list, config.white_list.get('filename', []))
        
        filename_buttons_layout = QHBoxLayout()
        add_filename_btn = QPushButton('添加')
        add_filename_btn.clicked.connect(lambda: self.add_list_item(self.filename_list, '文件名'))
        remove_filename_btn = QPushButton('删除')
        remove_filename_btn.clicked.connect(lambda: self.remove_list_item(self.filename_list))
        
        filename_buttons_layout.addWidget(add_filename_btn)
        filename_buttons_layout.addWidget(remove_filename_btn)
        
        filename_layout.addWidget(self.filename_list)
        filename_layout.addLayout(filename_buttons_layout)
        
        scroll_layout.addWidget(filename_group)
        
        # 后缀名白名单组
        suffix_group = QGroupBox("后缀名白名单")
        suffix_layout = QVBoxLayout(suffix_group)
        
        self.suffix_list = QListWidget()
        self.suffix_list.setMaximumHeight(120)
        self.load_list_items(self.suffix_list, config.white_list.get('suffix', []))
        
        suffix_buttons_layout = QHBoxLayout()
        add_suffix_btn = QPushButton('添加')
        add_suffix_btn.clicked.connect(lambda: self.add_list_item(self.suffix_list, '后缀名'))
        remove_suffix_btn = QPushButton('删除')
        remove_suffix_btn.clicked.connect(lambda: self.remove_list_item(self.suffix_list))
        
        suffix_buttons_layout.addWidget(add_suffix_btn)
        suffix_buttons_layout.addWidget(remove_suffix_btn)
        
        suffix_layout.addWidget(self.suffix_list)
        suffix_layout.addLayout(suffix_buttons_layout)
        
        scroll_layout.addWidget(suffix_group)
        
        # 让布局能够自然扩展
        scroll_layout.addStretch()
        
        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll)
        
        # 添加底部分割线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator2)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton('保存配置')
        save_btn.clicked.connect(self.save_config)
        reset_btn = QPushButton('重置为默认')
        reset_btn.clicked.connect(self.reset_to_default)
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.close)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def load_list_items(self, list_widget, items):
        """加载列表项到QListWidget"""
        list_widget.clear()
        for item in items:
            list_widget.addItem(str(item))
    
    def add_list_item(self, list_widget, item_type):
        """添加列表项"""
        text, ok = QInputDialog.getText(self, f'添加{item_type}', f'请输入{item_type}:')
        if ok and text:
            list_widget.addItem(text)
    
    def remove_list_item(self, list_widget):
        """删除选中的列表项"""
        selected_items = list_widget.selectedItems()
        for item in selected_items:
            list_widget.takeItem(list_widget.row(item))
    
    def browse_backup_dir(self):
        """浏览并选择备份目录"""
        directory = QFileDialog.getExistingDirectory(self, '选择备份目录', 
                                                     self.backup_path_edit.text())
        if directory:
            self.backup_path_edit.setText(directory)
    
    def save_config(self):
        """保存配置到YAML文件"""
        # 构建新的配置数据
        config_data = {
            'backup_dst': self.backup_path_edit.text(),
            'white_list': {
                'dirname': [self.dirname_list.item(i).text() for i in range(self.dirname_list.count())],
                'filename': [self.filename_list.item(i).text() for i in range(self.filename_list.count())],
                'suffix': [self.suffix_list.item(i).text() for i in range(self.suffix_list.count())]
            }
        }
        
        # 保存配置
        if config.save_config(config_data):
            QMessageBox.information(self, '成功', '配置已保存')
            config.reload()
        else:
            QMessageBox.critical(self, '错误', '保存配置失败')
    
    def reset_to_default(self):
        """重置为默认配置"""
        reply = QMessageBox.question(self, '确认', '确定要重置为默认配置吗?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if config.write_default():
                config.reload()
                # 更新UI
                self.backup_path_edit.setText(config.backup_dst)
                self.load_list_items(self.dirname_list, config.white_list.get('dirname', []))
                self.load_list_items(self.filename_list, config.white_list.get('filename', []))
                self.load_list_items(self.suffix_list, config.white_list.get('suffix', []))
                QMessageBox.information(self, '成功', '已重置为默认配置')
            else:
                QMessageBox.critical(self, '错误', '重置配置失败') 