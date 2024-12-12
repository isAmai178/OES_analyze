from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QFileDialog, QListWidget, QMessageBox
)
import sys

class FileUploader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('oxxo.studio')
# 設定主視窗
        self.setWindowTitle("檔案選擇與上傳")
        self.setGeometry(100, 100, 400, 300)

        # 初始化介面元件
        self.layout = QVBoxLayout()
        self.upload_button = QPushButton("選取檔案")
        self.file_list_widget = QListWidget()

        # 設定按鈕的點擊事件
        self.upload_button.clicked.connect(self.select_files)

        # 將元件加入佈局
        self.layout.addWidget(self.upload_button)
        self.layout.addWidget(self.file_list_widget)

        # 設定中心 Widget
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)    # 設定標籤文字
    def select_files(self):
            # 彈出檔案選取對話框
            files, _ = QFileDialog.getOpenFileNames(self, "選取檔案", "", "All Files (*.*)")

            if files:
                # 清空之前的檔案清單
                self.file_list_widget.clear()

                # 將選取的檔案名稱加入 ListWidget
                for file in files:
                    self.file_list_widget.addItem(file)

                # 顯示訊息框，告知上傳完成
                QMessageBox.information(self, "成功", f"已成功選取 {len(files)} 個檔案。")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileUploader()
    window.show()
    sys.exit(app.exec())
