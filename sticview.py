import os
import sys

import numpy as np

import matplotlib.pyplot as plt

from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, qApp

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):
        # ----- initialise window ----
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('STiC Viewer')

        # ----- initialise menubar ----
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('File')

        exitButton = QAction('Quit', self)
        exitButton.triggered.connect(qApp.quit)
        
        filemenu.addAction(exitButton)
       
        # ---- show GUI ----
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()

    sys.exit(app.exec_())
