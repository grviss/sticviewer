import os
import sys

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.cm as cm

from PyQt5.QtWidgets import (QMainWindow, QApplication, QAction, qApp,
QVBoxLayout, QFileDialog)
from PyQt5 import QtCore
import pyqtgraph as pg

import sparsetools as sp

from ipdb import set_trace as stop

def mplcm_to_pglut(cm_name):
    cmap = cm.get_cmap(cm_name)
    cmap._init()
    lut = (cmap._lut * 255).view(np.ndarray)
    return lut


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        pg.setConfigOptions(imageAxisOrder='row-major')

        # ---- get input ----
        self.filetypes = {\
             'atm': {'name': 'atmosout', 'fullname': 'atmosphere model',
             'filter': 'atmosout*.nc'},
             'syn': {'name': 'synthetic', 'fullname': 'synthetic profile',
             'filter': 'synthetic*.nc'},
             'obs': {'name': 'observed', 'fullname': 'observed profile',
             'filter': 'observed*.nc'}}
        self.fname_atmos = self.getFileName(typedict=self.filetypes['atm'])

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
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
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

        # Set cmaps
        self.img00.setLookupTable(mplcm_to_pglut('gist_heat'))
        self.img01.setLookupTable(mplcm_to_pglut('bwr'))
        self.img02.setLookupTable(mplcm_to_pglut('gist_gray'))
        self.img10.setLookupTable(mplcm_to_pglut('RdGy_r'))
        self.img11.setLookupTable(mplcm_to_pglut('Oranges'))
        self.img12.setLookupTable(mplcm_to_pglut('Greens'))

        # Add panels to GUI
        self.panel00.addItem(self.img00)
        self.panel01.addItem(self.img01)
        self.panel02.addItem(self.img02)
        self.panel10.addItem(self.img10)
        self.panel11.addItem(self.img11)
        self.panel12.addItem(self.img12)

        # Link panel views
        self.linkviews(self.panel00, self.panel01)
        self.linkviews(self.panel00, self.panel02)
        self.linkviews(self.panel00, self.panel10)
        self.linkviews(self.panel00, self.panel11)
        self.linkviews(self.panel00, self.panel12)

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
        self.m = sp.model(self.fname_atmos)
        self.nx = self.m.nx
        self.ny = self.m.ny
        self.itau = -1
        print("initModel: Model has dimensions (nx,ny)=({0},{1})".format(self.nx,
            self.ny))

        self.setlimits()

    def drawModel(self):
        self.img00.setImage(self.m.temp[0,:,:,self.itau])
        self.img01.setImage(self.m.vlos[0,:,:,self.itau])
        self.img02.setImage(self.m.vturb[0,:,:,self.itau])
        self.img10.setImage(self.m.Bln[0,:,:,self.itau])
        self.img11.setImage(self.m.Bho[0,:,:,self.itau])
        self.img12.setImage(self.m.azi[0,:,:,self.itau])

    def linkviews(self, anchorview, view):
        view.setXLink(anchorview)
        view.setYLink(anchorview)

    def setlimits(self):
        self.panel00.setLimits(xMin=0, xMax=self.nx, yMin=0, yMax=self.ny,
                minXRange=self.nx/10, minYRange=self.ny/10, maxXRange=self.nx,
                maxYRange=self.ny)
        self.panel01.setLimits(xMin=0, xMax=self.nx, yMin=0, yMax=self.ny,
                minXRange=self.nx/10, minYRange=self.ny/10, maxXRange=self.nx,
                maxYRange=self.ny)
        self.panel02.setLimits(xMin=0, xMax=self.nx, yMin=0, yMax=self.ny,
                minXRange=self.nx/10, minYRange=self.ny/10, maxXRange=self.nx,
                maxYRange=self.ny)
        self.panel10.setLimits(xMin=0, xMax=self.nx, yMin=0, yMax=self.ny,
                minXRange=self.nx/10, minYRange=self.ny/10, maxXRange=self.nx,
                maxYRange=self.ny)
        self.panel11.setLimits(xMin=0, xMax=self.nx, yMin=0, yMax=self.ny,
                minXRange=self.nx/10, minYRange=self.ny/10, maxXRange=self.nx,
                maxYRange=self.ny)
        self.panel12.setLimits(xMin=0, xMax=self.nx, yMin=0, yMax=self.ny,
                minXRange=self.nx/10, minYRange=self.ny/10, maxXRange=self.nx,
                maxYRange=self.ny)

    def getFileName(self, typedict=None):
        inam = 'getFileName'
        filename, _ = QFileDialog.getOpenFileName(self, 
            "Please select the input {0} file".format(typedict['name']), os.getcwd(), 
            "STiC {0} file ({1})".format(typedict['fullname'],
                typedict['filter']))
        if filename:
            print("{0}: opening {1} file {2}".format(inam, typedict['fullname'],
                filename))
            return filename
        else:
            print("{0} [error]: {1} file required to launch " \
                    "STiCViewer".format(inam, typedict['fullname']))
            sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()

    sys.exit(app.exec_())
