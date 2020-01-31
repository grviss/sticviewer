# -*- coding: utf8 -*-

import os
import sys

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.cm as cm

from PyQt5.QtWidgets import (QMainWindow, QApplication, QAction, qApp,
QVBoxLayout, QFileDialog, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
QSlider, QLabel, QGridLayout, QSpacerItem, QSizePolicy)
from PyQt5 import QtCore
import pyqtgraph as pg

import sparsetools as sp

from ipdb import set_trace as stop

def mplcm_to_pglut(cm_name):
    cmap = cm.get_cmap(cm_name)
    cmap._init()
    lut = (cmap._lut * 255).view(np.ndarray)
    return lut

class CWImage(QWidget):
    def __init__(self, canvas, row=0, col=0, cm_name='gist_gray', ch_color='w', nx=None,
            ny=None, parent=None):
        super(CWImage, self).__init__(parent=parent)
        self.box = canvas.addPlot(row=row, col=col)
        self.img = pg.ImageItem()
        self.img.setLookupTable(mplcm_to_pglut(cm_name))

        self.box.addItem(self.img)
        if (parent is not None):
            self.box.setLimits(xMin=0, xMax=parent.nx, yMin=0, yMax=parent.ny,
                    minXRange=parent.nx/10, minYRange=parent.ny/10,
                    maxXRange=parent.nx, maxYRange=parent.ny)

        # Handle crosshairs
        self.vLine = pg.InfiniteLine(pen=pg.mkPen(ch_color), angle=90, movable=False)
        self.hLine = pg.InfiniteLine(pen=pg.mkPen(ch_color), angle=0, movable=False)
        self.box.addItem(self.vLine, ignoreBounds=True)
        self.box.addItem(self.hLine, ignoreBounds=True)

        self.vLine.setPos(parent.nx/2)
        self.hLine.setPos(parent.ny/2)

        self.nx = parent.nx
        self.ny = parent.ny

        self.proxy = pg.SignalProxy(self.box.scene().sigMouseMoved, rateLimit=60,
                    slot=self.mouseMoved)

    def mouseMoved(self, event):
        pos = event[0]
        if self.box.sceneBoundingRect().contains(pos):
            mousePoint = self.box.vb.mapSceneToView(pos)
            self.xx = np.int(np.round(mousePoint.x()))
            self.yy = np.int(np.round(mousePoint.y()))
            # Ensure crosshairs within map
            self.xx = 0 if self.xx < 0 else self.nx-1 if self.xx >= self.nx else self.xx
            self.yy = 0 if self.yy < 0 else self.ny-1 if self.yy >= self.ny else self.yy
            # Export cursor position 
            self.parent().xx = self.xx
            self.parent().yy = self.yy
            # Update plots and crosshairs
            self.parent().plotModel()
            self.parent().plotSynth()
            self.parent().plotObs()
            self.parent().updateCrosshairs()

class CWPlot(QWidget):
    def __init__(self, canvas, row=0, col=0, plotwidth=200, xGrid=False,
            yGrid=False, xtitle=None, ytitle=None, addMarker=False, parent=None):
        super(CWPlot, self).__init__(parent=parent)
        self.box = canvas.addPlot(row=row, col=col)
        self.obsplot = self.box.plot()
        self.invplot = self.box.plot()
        self.box.setFixedWidth(plotwidth)
        self.box.showGrid(x=xGrid, y=yGrid)
        if xtitle is not None:
            self.box.setLabel('bottom', xtitle)
        if ytitle is not None:
            self.box.setLabel('left', xtitle)

        if addMarker is True:
            self.line = pg.InfiniteLine(angle=90, movable=False)
            self.box.addItem(self.line)



class Slider(QWidget):
    def __init__(self, label, vmin, vmax, step, initval, intslider=False, parent=None):
        super(Slider, self).__init__(parent=parent)
        # Create elements
        self.slider = QSlider(self)
        self.labelname = QLabel(self)
        self.labelvalue = QLabel(self)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setSingleStep(step)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.labelname)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.labelvalue)

        self.vmin = vmin
        self.vmax = vmax
        if self.vmax == self.vmin:
            self.vmax += 1
        self.sval = None

        if intslider is True:
            self.slider.setMinimum(self.vmin)
            self.slider.setMaximum(self.vmax)
            self.slider.valueChanged.connect(self.getValue)
            self.setValue(initval)
        else:
            self.slider.valueChanged.connect(self.getFValue)
            self.setFValue(initval)

        self.labelname.setText(label)

    def getValue(self, value):
        self.sval = np.int(self.vmin + (float(self.slider.value()) /
            np.abs(self.slider.maximum() - self.slider.minimum())) * np.abs(self.vmax -
                self.vmin))
        self.setLabelValue(intslider=True)

    def setValue(self, value):
        self.sval = value
        slidervalue = np.int((self.sval - self.vmin) / np.abs(self.vmax - self.vmin) \
            * np.abs(self.slider.maximum() - self.slider.minimum()))
        self.slider.setValue(slidervalue)
        self.setLabelValue(intslider=True)

    def getFValue(self, value):
        self.sval = self.vmin + (float(self.slider.value()) /
            np.abs(self.slider.maximum() - self.slider.minimum())) * np.abs(self.vmax -
                self.vmin)
        self.setLabelValue()

    def setFValue(self, value):
        self.sval = value
        slidervalue = (self.sval - self.vmin) / np.abs(self.vmax - self.vmin) \
            * np.abs(self.slider.maximum() - self.slider.minimum())
        self.slider.setValue(slidervalue)
        self.setLabelValue()

    def setLabelValue(self, intslider=False):
        if intslider is False:
            self.labelvalue.setText("{0:.4g}".format(self.sval))
        else:
            self.labelvalue.setText("{0}".format(self.sval))


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
             'filter': '*.nc'}}
        self.fname_atmos = self.getFileName(typedict=self.filetypes['atm'])
        self.fname_synth = self.getFileName(typedict=self.filetypes['syn'])
        self.fname_obs = self.getFileName(typedict=self.filetypes['obs'])

        # ---- initialise input ----
        self.initModel()
        self.initSynth()
        self.initObs()

        # ---- initialise UI ----
        self.initUI()

        # ---- initial draw ----
        self.drawModel()
        self.drawSynth()
        self.drawObs()
        self.plotModel()
        self.plotObs()
        self.plotSynth()


    def initUI(self):
        # ----- initialise window ----
        self.setGeometry(0, 0, 1400, 1000)
        self.setWindowTitle('STiC Viewer')

        # ---- set up control panel ----
        cpanel_layout = QVBoxLayout()

        self.zslider = Slider('Optical depth [log('+u"τ"+'])', self.ltaus.min(),
                self.ltaus.max(), np.diff(self.ltaus).mean()/2.,
                self.ltaus[self.itau])
        self.zslider.slider.valueChanged.connect(self.updateDepth)
        self.tslider = Slider('Time [index]', 0, self.nt-1, 1, 0, intslider=True)
        if self.nt:
            self.tslider.setDisabled(True)
        self.tslider.slider.valueChanged.connect(self.updateTime)

        self.wslider = Slider('Wavelength [index]', 0, self.nw-1, 1, 0,
                intslider=True)
        self.wslider.slider.valueChanged.connect(self.updateWave)

        cpanel_layout.addWidget(self.zslider)
        cpanel_layout.addWidget(self.tslider)
        cpanel_layout.addWidget(self.wslider)
        spacerItem = QSpacerItem(50, 50, QSizePolicy.Minimum,
                QSizePolicy.Expanding)
        cpanel_layout.addItem(spacerItem)

        cpanel = QWidget()
        cpanel.setLayout(cpanel_layout)
        cpanel.setFixedWidth(250)

        # ---- initialise canvas ----
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.invpen = pg.mkPen('r', width=3)

        self.icanvas = pg.GraphicsLayoutWidget()
        self.pcanvas = pg.GraphicsLayoutWidget()
        self.pcanvas.setFixedWidth(600)
#        self.setCentralWidget(self.canvas)
        layout = QHBoxLayout()
        layout.addWidget(cpanel)
        layout.addWidget(self.icanvas)
        layout.addWidget(self.pcanvas)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        rows = [0, 0, 0, 1, 1, 1, 2, 2, 2]
        cols = [0, 1, 2] * 3
        cm_names = ['gist_heat', 'bwr', 'gist_gray', 'RdGy_r', 'Oranges',
        'Greens', 'gist_gray', 'Blues_r', 'copper']
        ch_colors = ['w', 'k', 'w', 'k', 'k', 'k', 'w', 'k', 'w']

        self.cwimages = []
        for ii in range(len(cols)):
            cwimage = CWImage(self.icanvas, row=rows[ii], col=cols[ii],
                    cm_name=cm_names[ii], ch_color=ch_colors[ii], parent=self)
            self.cwimages.append(cwimage)

        for ii in range(len(cols)-1):
            self.linkviews(self.cwimages[0].box, self.cwimages[ii+1].box)

        # Fill plot canvas
        rows = [0, 0, 1, 1, 2, 2]
        cols = [0, 1] * 3
        xtitles_mod = ['log('+u"τ"+')'] * 2
        xtitles_obs = ['wavelength'] * 4
        xtitles = xtitles_mod + xtitles_obs
        ytitles_mod = ['T [kK]', 'v_los [km/s]']
        ytitles_obs = ['scaled intensity'] * 4
        ytitles = ytitles_mod + ytitles_obs
        self.cwplots = []
        for ii in range(len(cols)):
            cwplot = CWPlot(self.pcanvas, row=rows[ii], col=cols[ii],
                    xGrid=True, yGrid=True, addMarker=(ii >= 2), plotwidth=275,
                    xtitle=xtitles[ii], ytitle=ytitles[ii])
            self.cwplots.append(cwplot)

        # Link plot panel views
        self.cwplots[1].box.setXLink(self.cwplots[0].box)
        for ii in range(3):
            self.cwplots[ii+3].box.setXLink(self.cwplots[2].box)

        self.updateWMarker()

        # ----- initialise menubar ----
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('File')

        exitButton = QAction('Quit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.triggered.connect(qApp.quit)
        filemenu.addAction(exitButton)

        # ---- show GUI ----
        self.show()

    def initModel(self):
        self.m = sp.model(self.fname_atmos)
        self.nx = self.m.nx
        self.ny = self.m.ny
        self.itau = -1
        self.tt = 0
        self.xx = np.int(self.nx/2)
        self.yy = np.int(self.ny/2)
        self.nt = self.m.nt
        self.ltaus = self.m.ltau[0,0,0,:]

        self.m.azi *= 180./np.pi
        self.m.vturb *= 1.e-5
        self.m.vlos *= 1.e-5
        print("initModel: Model has dimensions (nx,ny)=({0},{1})".format(self.nx,
            self.ny))

    def initSynth(self):
        self.s = sp.profile(self.fname_synth)
        self.wsel = np.where(self.s.dat[0,0,0,:,0] > 0)[0]
        self.synprof = self.s.dat[:,:,:,self.wsel,:]
        self.wav = self.s.wav
        self.nw = self.wsel.size
        self.ww = 0
        self.istokes = 0

    def initObs(self):
        self.o = sp.profile(self.fname_obs)
        self.obsprof = self.o.dat[:,:,:,self.wsel,:]
        self.chi2 = (self.obsprof - self.synprof)**2
        tt, yy, xx, ww, ss = np.where(self.synprof != 0)
        self.chi2[tt,yy,xx,ww,ss] /= self.synprof[tt,yy,xx,ww,ss]
        chi2max = self.chi2.max()
        tt, yy, xx, ww, ss = np.where(self.synprof == 0)
        self.chi2[tt,yy,xx,ww,ss] = chi2max
        self.chi2 = np.sum(self.chi2, axis=3)


    def drawModel(self):
        self.cwimages[0].img.setImage(self.m.temp[self.tt,:,:,self.itau])
        self.cwimages[1].img.setImage(self.m.vlos[self.tt,:,:,self.itau])
        self.cwimages[2].img.setImage(self.m.vturb[self.tt,:,:,self.itau])
        self.cwimages[3].img.setImage(self.m.Bln[self.tt,:,:,self.itau])
        self.cwimages[4].img.setImage(self.m.Bho[self.tt,:,:,self.itau])
        self.cwimages[5].img.setImage(self.m.azi[self.tt,:,:,self.itau])

    def plotModel(self):
        self.cwplots[0].invplot.setData(self.ltaus, self.m.temp[self.tt,self.yy,self.xx,:]/1.e3,
                pen=self.invpen)
        self.cwplots[1].invplot.setData(self.ltaus, self.m.vlos[self.tt,self.yy,self.xx,:],
                pen=self.invpen)

    def drawSynth(self):
        self.cwimages[7].img.setImage(self.synprof[self.tt,:,:,self.ww,self.istokes])

    def plotSynth(self):
        for ii in range(4):
            self.cwplots[ii+2].invplot.setData(self.wav,
                    self.synprof[self.tt,self.yy,self.xx,:,ii], pen=self.invpen)

    def drawObs(self):
        self.cwimages[6].img.setImage(self.obsprof[self.tt,:,:,self.ww,self.istokes])
        self.cwimages[8].img.setImage(self.chi2[self.tt,:,:, self.istokes])

    def plotObs(self):
        for ii in range(4):
            self.cwplots[ii+2].obsplot.setData(self.wav,
                    self.obsprof[self.tt,self.yy,self.xx,:,ii], symbol='o',
                    symbolPen='k')

    def linkviews(self, anchorview, view):
        view.setXLink(anchorview)
        view.setYLink(anchorview)

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

    def updateDepth(self):
        self.itau = np.argmin(np.abs(self.ltaus-self.zslider.sval))
        self.drawModel()

    def updateTime(self):
        self.tt = self.tslider.sval
        self.drawModel()
        self.drawSynth()
        self.drawObs()
        self.plotModel()

    def updateWave(self):
        self.ww = self.wslider.sval
        self.drawSynth()
        self.drawObs()
        self.updateWMarker()

    def updateWMarker(self):
        for ii in range(4):
            self.cwplots[ii+2].line.setPos(self.wav[self.ww])

    def updateCrosshairs(self):
        for ii in range(len(self.cwimages)):
            self.cwimages[ii].vLine.setPos(self.xx+0.5) # +0.5: place mid-pixel
            self.cwimages[ii].hLine.setPos(self.yy+0.5)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()

    sys.exit(app.exec_())
