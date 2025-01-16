import sys
from PyQt6.QtWidgets import QApplication
from OES_GUI import OESAnalyzerGUI

def main():
    app = QApplication(sys.argv)
    
    # 設置應用程式樣式
    app.setStyle('Fusion')
    window = OESAnalyzerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()