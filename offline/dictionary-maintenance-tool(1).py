import sys
import os
from datetime import datetime
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
                             QComboBox, QFileDialog, QInputDialog)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class DictionaryMaintenanceTool(QMainWindow):
    def __init__(self):
        super().__init__()
        # characters の初期化を __init__ メソッドに移動
        self.characters = list('abcdefghijklmnopqrstuvwxyz0123456789') + list('.,')
        self.initUI()
        self.dictionary = {}
        self.current_file = ""
        self.sort_option = 'default'

    def initUI(self):
        self.setWindowTitle('辞書メンテナンスツール')
        self.setGeometry(100, 100, 800, 600)

        # メインウィジェット
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # ファイル名表示
        self.file_label = QLabel('辞書ファイル: 未選択')
        main_layout.addWidget(self.file_label)

        # フォントサイズドロップダウン
        font_layout = QHBoxLayout()
        font_label = QLabel('フォントサイズ:')
        self.font_combo = QComboBox()
        self.font_combo.addItems(['8', '10', '12', '14', '16'])
        self.font_combo.setCurrentText('12')
        self.font_combo.currentTextChanged.connect(self.change_font_size)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_combo)
        font_layout.addStretch()

        main_layout.addLayout(font_layout)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.characters))
        self.table.setRowCount(len(self.characters))
        
        # ヘッダー設定
        self.table.setHorizontalHeaderLabels(self.characters)
        self.table.setVerticalHeaderLabels(self.characters)

        main_layout.addWidget(self.table)

        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        # 各種ボタン
        buttons = [
            ('辞書読込', self.load_dictionary),
            ('書出', self.save_dictionary),
            ('名前を付けて保存', self.save_dictionary_as)
        ]

        for label, method in buttons:
            btn = QPushButton(label)
            btn.clicked.connect(method)
            button_layout.addWidget(btn)

        # ソートオプション
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['デフォルト順', 'あいうえお末尾'])
        self.sort_combo.currentIndexChanged.connect(self.update_table_order)
        button_layout.addWidget(self.sort_combo)

        main_layout.addLayout(button_layout)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    # 以下、先ほどのコードと同じ

def main():
    app = QApplication(sys.argv)
    ex = DictionaryMaintenanceTool()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
