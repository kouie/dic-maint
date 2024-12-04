import sys
import os
import re
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
                             QComboBox, QFileDialog, QLineEdit, QCheckBox, QDialog, 
                             QDialogButtonBox, QFormLayout)
from PyQt5.QtGui import QFont, QValidator
from PyQt5.QtCore import Qt, QRegExp

class JapaneseInputValidator(QValidator):
    def validate(self, input_text, pos):
        # 全角文字のみを許可
        if re.match(r'^[^\x00-\x7F]+$', input_text):
            return QValidator.Acceptable, input_text, pos
        return QValidator.Invalid, input_text, pos

class EditDialog(QDialog):
    def __init__(self, parent=None, current_value=''):
        super().__init__(parent)
        self.setWindowTitle('エントリ編集')
        layout = QFormLayout()
        
        # 全角文字のバリデータを設定
        validator = JapaneseInputValidator()
        
        self.input = QLineEdit()
        self.input.setText(current_value)
        self.input.setValidator(validator)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addRow('新しい値:', self.input)
        layout.addRow(buttons)
        
        self.setLayout(layout)

class DictionaryMaintenanceTool(QMainWindow):
    def __init__(self):
        super().__init__()
        # 辞書の文字セットを動的に生成するための変更
        self.base_characters = list('abcdefghijklmnopqrstuvwxyz0123456789')
        self.additional_characters = []
        self.characters = self.base_characters.copy()
        
        self.initUI()
        self.dictionary = {}
        self.current_file = ""
        self.sort_option = 'default'

    def initUI(self):
        self.setWindowTitle('辞書メンテナンスツール')
        self.setGeometry(100, 100, 800, 600)

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
        
        # テーブルのダブルクリックイベント
        self.table.cellDoubleClicked.connect(self.edit_cell)

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

        # エントリ順維持チェックボックス
        self.maintain_order_checkbox = QCheckBox('現在のエントリ順を維持')
        self.maintain_order_checkbox.setChecked(True)
        button_layout.addWidget(self.maintain_order_checkbox)

        main_layout.addLayout(button_layout)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def edit_cell(self, row, col):
        # 読みを取得
        row_char = self.characters[row]
        col_char = self.characters[col]
        key = row_char + col_char

        # 現在の値を取得
        current_value = self.dictionary.get(key, '')

        # 編集ダイアログを表示
        dialog = EditDialog(self, current_value)
        if dialog.exec_() == QDialog.Accepted:
            new_value = dialog.input.text()
            
            # 空白の場合は削除
            if new_value:
                self.dictionary[key] = new_value
            else:
                self.dictionary.pop(key, None)

            # テーブルを更新
            self.update_table()

    def load_dictionary(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Dictionary File', '', 'Text Files (*.txt)')
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f'辞書ファイル: {file_path}')
            self.read_dictionary(file_path)

    def read_dictionary(self, file_path):
        self.dictionary.clear()
        # 追加文字をリセット
        self.additional_characters = []

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    reading, word = line.split('=')
                    
                    # 追加の文字を検出
                    for char in reading:
                        if char not in self.base_characters and char not in self.additional_characters:
                            self.additional_characters.append(char)
                    
                    # 全ての読みを保持
                    self.dictionary[reading] = word

        # キャラクターリストを更新
        self.characters = self.base_characters + self.additional_characters
        self.update_table_setup()
        self.update_table()

    def update_table_setup(self):
        # テーブルの再設定
        self.table.setColumnCount(len(self.characters))
        self.table.setRowCount(len(self.characters))
        
        # ヘッダー設定
        self.table.setHorizontalHeaderLabels(self.characters)
        self.table.setVerticalHeaderLabels(self.characters)

    def update_table(self):
        # テーブルをクリア
        self.table.clearContents()

        # 文字リストを取得（ソートオプションに応じて）
        current_chars = self.get_sorted_characters()

        for row, row_char in enumerate(current_chars):
            for col, col_char in enumerate(current_chars):
                key = row_char + col_char
                if key in self.dictionary:
                    item = QTableWidgetItem(self.dictionary[key])
                    self.table.setItem(row, col, item)

    def get_sorted_characters(self):
        chars = self.base_characters + self.additional_characters
        
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
        with open(file_path, 'w', encoding='utf-8-sig', newline='\r\n') as f:
            # エントリ順序の制御
            if not self.maintain_order_checkbox.isChecked():
                # 2文字のエントリを先に書き出し、その後3文字以上のエントリを書き出す
                two_char_entries = {k: v for k, v in self.dictionary.items() if len(k) == 2}
                other_entries = {k: v for k, v in self.dictionary.items() if len(k) > 2}
                
                for key, value in two_char_entries.items():
                    f.write(f'{key}={value}\n')
                
                for key, value in other_entries.items():
                    f.write(f'{key}={value}\n')
            else:
                # 現在のエントリ順序を維持
                for key, value in self.dictionary.items():
                    f.write(f'{key}={value}\n')

def main():
    app = QApplication(sys.argv)
    ex = DictionaryMaintenanceTool()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
