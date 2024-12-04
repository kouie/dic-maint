import sys
import os
import re
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
                             QComboBox, QFileDialog, QLineEdit, QCheckBox, QDialog, 
                             QDialogButtonBox, QFormLayout, QMessageBox)
from PyQt5.QtGui import QFont, QValidator, QColor
from PyQt5.QtCore import Qt, QRegExp

class JapaneseInputValidator(QValidator):
    def validate(self, input_text, pos):
        # 全角文字のみを許可
        if pos == 0:
            return QValidator.Acceptable, input_text, pos   #type: ignore
        if re.match(r'^[^\x00-\x7F]+$', input_text):
            return QValidator.Acceptable, input_text, pos   #type: ignore
        return QValidator.Invalid, input_text, pos   #type: ignore

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
        
        self.dictionary = {}
        self.current_file = ""
        self.sort_option = 'default'
        self.duplicated_items = {}
        self.original_lines = []
        self.key_filter = {'pos':'0', 'chr':''}
        self.initUI()

    def initUI(self):
        self.setWindowTitle('辞書メンテナンスツール')
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        load_file_layout = QHBoxLayout()

        # ファイル名表示
        self.load_button = QPushButton('辞書選択')
        self.load_button.clicked.connect(self.load_dictionary)
        self.load_button.setFixedSize(100,22)
        load_file_layout.addWidget(self.load_button)

        self.file_label = QLabel('辞書ファイル: 未選択')
        load_file_layout.addWidget(self.file_label)

        main_layout.addLayout(load_file_layout)

        # フォントサイズドロップダウン
        operation_layout = QHBoxLayout()

        filter_char_label = QLabel('1 文字目:')
        self.filter_char_combo = QComboBox()
        self.filter_char_combo.addItems(['2文字'])
        self.filter_char_combo.addItems(self.get_sorted_characters())
        self.filter_char_combo.setCurrentText('2文字')
        self.filter_char_combo.currentTextChanged.connect(self.change_filter_character)
        operation_layout.addWidget(filter_char_label)
        operation_layout.addWidget(self.filter_char_combo)


        operation_layout.addStretch()

        font_label = QLabel('フォントサイズ:')
        self.font_combo = QComboBox()
        self.font_combo.addItems(['8', '10', '12', '14', '16'])
        self.font_combo.setCurrentText('12')
        self.font_combo.currentTextChanged.connect(self.change_font_size)
        operation_layout.addWidget(font_label)
        operation_layout.addWidget(self.font_combo)

        # ソートオプション
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['デフォルト順', 'あいうえお末尾'])
        self.sort_combo.currentIndexChanged.connect(self.update_table_order)
        operation_layout.addWidget(self.sort_combo)

        main_layout.addLayout(operation_layout)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.characters))
        self.table.setRowCount(len(self.characters))

        font = QFont()
        font.setPointSize(12)
        self.table.setFont(font)
        self.table.resizeColumnsToContents()

        # テーブルのダブルクリックイベント
        self.table.cellDoubleClicked.connect(self.edit_cell)

        main_layout.addWidget(self.table)

        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        # 各種ボタン
        buttons = [
            ('上書き保存', self.save_dictionary),
            ('名前を付けて保存', self.save_dictionary_as)
        ]

        for label, method in buttons:
            btn = QPushButton(label)
            btn.clicked.connect(method)
            button_layout.addWidget(btn)

        # エントリ順維持チェックボックス
#        self.maintain_order_checkbox = QCheckBox('現在のエントリ順を維持')
#        self.maintain_order_checkbox.setChecked(True)
#        button_layout.addWidget(self.maintain_order_checkbox)
#
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def edit_cell(self, row, col):
        current_chars = self.get_sorted_characters()        
        # 読みを取得
        row_char = current_chars[row]
        col_char = current_chars[col]
        key = row_char + col_char

        key = self.get_original_key(key)

        # 現在の値を取得
        if key in self.duplicated_items:
            current_value = ''
            for value in self.duplicated_items[key]:
                current_value = current_value + '／' + value
            current_value = current_value[1:]
        else:
            current_value = self.dictionary.get(key, '')

        # 編集ダイアログを表示
        dialog = EditDialog(self, current_value)
        if dialog.exec_() == QDialog.Accepted:
            new_value = dialog.input.text()
            self.dictionary[key] = new_value

            if key in self.duplicated_items:
                self.duplicated_items.pop(key)

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
        self.duplicated_items.clear()
        
        # 追加文字をリセット
        self.additional_characters = []
        self.original_lines = []

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                self.original_lines.append(line)
                if '=' in line:
                    reading, word = line.split('=')
                    
                    # 追加の文字を検出
                    for char in reading:
                        if char not in self.base_characters and char not in self.additional_characters:
                            self.additional_characters.append(char)
                    
                    # 登録済み (重複している) かどうか
                    if reading in self.dictionary:
                        if reading in self.duplicated_items:
                            registered = self.duplicated_items[reading]
                        else:
                            registered = [self.dictionary[reading]]

                        registered.extend(word)
                        self.duplicated_items[reading] = registered

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

        self.table.setHorizontalHeaderLabels(current_chars)
        self.table.setVerticalHeaderLabels(current_chars)

        for row, row_char in enumerate(current_chars):
            for col, col_char in enumerate(current_chars):
                key = row_char + col_char
                key = self.get_original_key(key)

                if key in self.dictionary:
                    word = self.dictionary[key]
                else:
                    word = ''
                item = QTableWidgetItem(word)
                if row % 2 == 0:
                    item.setBackground(QColor("white")) 
                else:
                    item.setBackground(QColor(245,245,245))
                self.table.setItem(row, col, item)

        self.update_duplicated()
        self.table.resizeColumnsToContents()

    def get_original_key(self, key: str) -> str:
        pos = int(self.key_filter['pos'])
        chr = self.key_filter['chr']
        key = key[:pos] + chr + key[pos:]

        return key

    def update_duplicated(self):
        pos = int(self.key_filter['pos'])
        chr = self.key_filter['chr']
        if chr == '':
            targets = {k:v for k, v in self.duplicated_items.items() if len(k) == 2}
        else:
            targets = {k:v for k, v in self.duplicated_items.items() if k[0] == chr and len(k) == 3}

        current_chars = self.get_sorted_characters()

        for key, value in targets.items():
            key = key.zfill(3)[pos+1:]

            row = current_chars.index(key[0])
            col = current_chars.index(key[1])
            words = ''
            for word in value:
                if words == '':
                    words = word
                else:
                    words = words + '/' + word
            item = QTableWidgetItem(words)
            item.setBackground(QColor(255,200,200))
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
        self.table.resizeColumnsToContents()

    def change_filter_character(self, chr: str):
        if chr == '2文字':
            self.key_filter['chr'] = ''
        else:
            self.key_filter['chr'] = chr
        self.update_table()

    def save_dictionary(self):
        if not self.current_file:
            self.save_dictionary_as()
            return

        self.create_backup(self.current_file)
        self.write_dictionary(self.current_file)

    def save_dictionary_as(self):
        if self.duplicated_items:
            response = QMessageBox.question(
                self,
                '重複データの確認',
                '読みが重複するデータが残っています。このまま保存しますか?',
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            if response == QMessageBox.Cancel:
                return

        file_path, _ = QFileDialog.getSaveFileName(self, '辞書ファイルを保存', '', 'Text Files (*.txt)')
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f'辞書ファイル: {file_path}')
            self.create_backup(file_path)
            self.write_dictionary(file_path)

    def create_backup(self, file_path):
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = 'mt_backup/'
            backup_path = os.path.join(
                os.path.dirname(file_path), 
                f'{backup_dir}{timestamp}_{os.path.basename(file_path)}'
            )
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            os.rename(file_path, backup_path)

    def write_dictionary(self, file_path):
        with open(file_path, 'w', encoding='utf-8-sig', newline='\r\n') as f:

            original_keys = []  # 元のファイルにあるキーのうち出力済みのものを記録
            
            for line in self.original_lines:
                if '=' in line:
                    reading, word = line.split('=')

                    if self.dictionary[reading] == '':
                        # エントリを削除したものはスキップ
                        original_keys.append(reading)
                        continue
                    if reading in list(self.duplicated_items):
                        # 重複が解決していないもの
                        if reading not in original_keys:
                            original_keys.append(reading)
                        out_line = line
                    elif reading in list(original_keys):
                        # 重複が解決したものはスキップ (2 番目以降)
                        continue
                    else:
                        # 重複していないものはテーブルの値で置き換えて出力
                        out_line = reading + '=' + self.dictionary[reading]
                        original_keys.append(reading)

                else:
                    # コメント等の無効な行もそのまま出力
                    out_line = line

                f.write(f'{out_line}\n')

            # 新しく追加したエントリをファイルの末尾に出力
            for key, value in self.dictionary.items():
                if key not in original_keys:
                    f.write(f'{key}={value}\n')

def main():
    app = QApplication(sys.argv)
    ex = DictionaryMaintenanceTool()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
