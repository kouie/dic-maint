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
        self.characters = list('abcdefghijklmnopqrstuvwxyz0123456789') + list('.,')
#        self.characters = list('bcdfghjklmnpqrstvwxyz0123456789aiueo') + list('.,')
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

    def load_dictionary(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Dictionary File', '', 'Text Files (*.txt)')
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f'辞書ファイル: {file_path}')
            self.read_dictionary(file_path)

    def read_dictionary(self, file_path):
        self.dictionary.clear()
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    reading, word = line.split('=')
                    if len(reading) == 2:
                        self.dictionary[reading] = word

        self.update_table()

    def update_table(self):
        # テーブルをクリア
        self.table.clearContents()

        # 文字リストを取得（ソートオプションに応じて）
        current_chars = self.get_sorted_characters()

        self.table.setHorizontalHeaderLabels(current_chars)
        self.table.setVerticalHeaderLabels(current_chars)

        for row, row_char in enumerate(current_chars):
            for col, col_char in enumerate(current_chars):
                key = row_char + col_char
                if key in self.dictionary:
                    item = QTableWidgetItem(self.dictionary[key])
                    self.table.setItem(row, col, item)

    def get_sorted_characters(self):
        chars = list('abcdefghijklmnopqrstuvwxyz0123456789') + list('.,')
#        chars = list('bcdfghjklmnpqrstvwxyz0123456789aiueo') + list('.,')
        
        if self.sort_option == 'aiueo_last':
            # あいうえおを末尾に移動
            vowels = ['a', 'i', 'u', 'e', 'o']
            non_vowels = [c for c in chars if c not in vowels]
            chars = non_vowels + vowels

        return chars

    def update_table_order(self, index):
        self.sort_option = 'aiueo_last' if index == 1 else 'default'
        self.update_table()

    def change_font_size(self, size):
        font = QFont()
        font.setPointSize(int(size))
        self.table.setFont(font)

    def save_dictionary(self):
        if not self.current_file:
            self.save_dictionary_as()
            return

        self.create_backup(self.current_file)
        self.write_dictionary(self.current_file)

    def save_dictionary_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, '辞書ファイルを保存', '', 'Text Files (*.txt)')
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f'辞書ファイル: {file_path}')
            self.create_backup(file_path)
            self.write_dictionary(file_path)

    def create_backup(self, file_path):
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(
                os.path.dirname(file_path), 
                f'{timestamp}_{os.path.basename(file_path)}'
            )
            os.rename(file_path, backup_path)

    def write_dictionary(self, file_path):
        # 2文字のエントリを先に書き出し、その後3文字以上のエントリを書き出す
        file_path = 'write-test.txt'
        with open(file_path, 'w', encoding='utf-8-sig', newline='\r\n') as f:
            # まず2文字のエントリを書き出し
            two_char_entries = {k: v for k, v in self.dictionary.items() if len(k) == 2}
            
            # その他のエントリ
            other_entries = {k: v for k, v in self.dictionary.items() if len(k) > 2}
            
            # 書き出し
            for key, value in two_char_entries.items():
                f.write(f'{key}={value}\n')
            
            for key, value in other_entries.items():
                f.write(f'{key}={value}\n')

def main():
    app = QApplication(sys.argv)
    ex = DictionaryMaintenanceTool()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
