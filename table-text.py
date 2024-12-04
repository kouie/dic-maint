from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PyQt5.QtGui import QColor

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # QTableWidgetを作成
        self.table = QTableWidget(10, 3)  # 10行3列
        self.table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        
        # 行の背景色を交互に設定
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = QTableWidgetItem(f"Row {row + 1}, Col {col + 1}")
                if row % 2 == 0:
                    item.setBackground(QColor("white"))  # 偶数行: 白
                else:
                    item.setBackground(QColor("lightgray"))  # 奇数行: グレー
                self.table.setItem(row, col, item)
        
        # レイアウト
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
