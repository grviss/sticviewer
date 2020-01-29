import os
import sys

import numpy as np

import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (QMainWindow, QApplication, QAction, qApp,
QVBoxLayout)
import pyqtgraph as pg

import sparsetools as sp

class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        pg.setConfigOptions(imageAxisOrder='row-major')

        # ---- process input ----
        self.mfile = sys.argv[1]

        # ---- initialise UI ----
        self.initUI()

        # ---- initialise UI ----
        self.initModel()

        # ---- initial draw ----
        self.drawModel()
#        self.canvas.draw()


    def initUI(self):
        # ----- initialise window ----
        self.setGeometry(0, 0, 1200, 1000)
        self.setWindowTitle('STiC Viewer')


        # ---- initialise canvas ----
        self.canvas = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.canvas)
        # row 0
        self.panel00 = self.canvas.addPlot(row=0, col=0)
        self.panel01 = self.canvas.addPlot(row=0, col=1)
        self.panel02 = self.canvas.addPlot(row=0, col=2)
        # row 1
        self.panel10 = self.canvas.addPlot(row=1, col=0)
        self.panel11 = self.canvas.addPlot(row=1, col=1)
        self.panel12 = self.canvas.addPlot(row=1, col=2)
        # Place ImageItem() into plot windows
        self.img00 = pg.ImageItem()
        self.img01 = pg.ImageItem()
        self.img02 = pg.ImageItem()
        self.img10 = pg.ImageItem()
        self.img11 = pg.ImageItem()
        self.img12 = pg.ImageItem()

        # Add panels to GUI
        self.panel00.addItem(self.img00)
        self.panel01.addItem(self.img01)
        self.panel02.addItem(self.img02)
        self.panel10.addItem(self.img10)
        self.panel11.addItem(self.img11)
        self.panel12.addItem(self.img12)

        # ----- initialise menubar ----
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('File')

        exitButton = QAction('Quit', self)
        exitButton.triggered.connect(qApp.quit)
        filemenu.addAction(exitButton)
       
        # ---- show GUI ----
        self.show()

    def initModel(self):
        self.m = sp.model(self.mfile)
        self.nx = self.m.nx
        self.ny = self.m.ny
        self.itau = -1
        print("initModel: Model has dimensions (nx,ny)=({0},{1})".format(self.nx,
            self.ny))

    def drawModel(self):
        self.img00.setImage(self.m.temp[0,:,:,self.itau])
        self.img01.setImage(self.m.vlos[0,:,:,self.itau])
        self.img02.setImage(self.m.vturb[0,:,:,self.itau])
        self.img10.setImage(self.m.Bln[0,:,:,self.itau])
        self.img11.setImage(self.m.Bho[0,:,:,self.itau])
        self.img12.setImage(self.m.azi[0,:,:,self.itau])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()

    sys.exit(app.exec_())