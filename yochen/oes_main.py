#!/usr/bin/env python3
import sys
from oes_gui import OESAnalyzerGUI
from PyQt6.QtWidgets import QApplication

def main():
    # 建立 QApplication 實例
    app = QApplication(sys.argv)
    
    try:
        # 建立並顯示主視窗
        window = OESAnalyzerGUI()
        window.show()
        
        # 執行應用程式
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 