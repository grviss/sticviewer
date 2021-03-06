# -*- coding: utf8 -*-

import os
import sys

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap

#from ipdb import set_trace as stop

if sys.version_info[0] < 3:
    raise SystemExit('Error: Python 3 or later is required to run STiCViewer')

try:
    from PyQt5 import QtCore
except ImportError:
    raise SystemExit('ImportError: PyQt5 is required to run STiCViewer')
else:
    from PyQt5.QtWidgets import (QMainWindow, QApplication, QAction, qApp,
    QVBoxLayout, QFileDialog, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QSlider, QLabel, QGridLayout, QSpacerItem, QSizePolicy, QRadioButton,
    QButtonGroup, QGroupBox)

try:
    import pyqtgraph as pg
except ImportError:
    raise SystemExit('ImportError: pyqtgraph is required to run STiCViewer')

try:
    import sparsetools as sp
except ImportError:
    raise SystemExit('ImportError: sparsetools (comes with STiC distribution) is required to run STiCViewer')

def mplcm_to_pglut(cmap):
    cmap._init()
    lut = (cmap._lut * 255).view(np.ndarray)[:256,:]
    return lut

def cmap_truncate(cmap, absmax=1.0, minmax=[0.1,0.9], n=256):
    # from https://stackoverflow.com/questions/18926031/how-to-extract-a-subset-of-a-colormap-as-a-new-colormap-in-matplotlib
    minmax_all = [-1.*absmax, absmax]
    drange = np.diff(minmax_all)[0]
    minval = (minmax[0]-minmax_all[0])/drange
    maxval = 1.-(minmax_all[1]-minmax[1])/drange
    new_cmap = LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap


class CWImage(QWidget):
    def __init__(self, canvas, row=0, col=0, cm_name='gist_gray', ch_color='w', nx=None,
            ny=None, xtitle=None, ytitle=None, parent=None):
        super(CWImage, self).__init__(parent=parent)
        self.box = canvas.addPlot(row=row, col=col)
        self.img = pg.ImageItem()
        self.img.setLookupTable(mplcm_to_pglut(cm_name))
        if xtitle is not None:
            self.box.setLabel('bottom', xtitle)
        if ytitle is not None:
            self.box.setLabel('left', ytitle)

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
        self.invplot2 = self.box.plot()
        self.box.setFixedWidth(plotwidth)
        self.box.showGrid(x=xGrid, y=yGrid)
        if xtitle is not None:
            self.box.setLabel('bottom', xtitle)
        if ytitle is not None:
            self.box.setLabel('left', ytitle)

        if addMarker is True:
            self.line = pg.InfiniteLine(pen=pg.mkPen('b'), angle=90, movable=False)
            self.box.addItem(self.line)


class Slider(QWidget):
    def __init__(self, label, vmin, vmax, step, initval, values=None, units='', intslider=False, parent=None):
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
        self.values = values
        self.units = units

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
            self.labelvalue.setText("{0:.2f}".format(self.sval))
        elif self.values is not None:
            self.labelvalue.setText("{0}: {1:.2f}{2}".format(self.sval,
                self.values[self.sval], self.units))
        else:
            self.labelvalue.setText("{0}".format(self.sval))


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        pg.setConfigOptions(imageAxisOrder='row-major')

        # ---- get input ----
        self.cwd = os.getcwd()
        if len(sys.argv) == 4:
            self.fname_obs, self.fname_synth, self.fname_atmos = sys.argv[1:]
        else:
            self.filetypes = {\
                 'atm': {'name': 'atmosout', 'fullname': 'atmosphere model',
                 'filter': '*.nc'},
                 'syn': {'name': 'synthetic', 'fullname': 'synthetic profile',
                 'filter': '*.nc'},
                 'obs': {'name': 'observed', 'fullname': 'observed profile',
                 'filter': '*.nc'}}
            self.fname_obs = self.getFileName(typedict=self.filetypes['obs'])
            self.fname_synth = self.getFileName(typedict=self.filetypes['syn'])
            self.fname_atmos = self.getFileName(typedict=self.filetypes['atm'])

        # ---- initialise input ----
        self.initObs()
        self.initModel()
        self.initSynth()
        self.getChi2()
        self.vminmaxImage()

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

        self.zslider = Slider('Optical depth [index: log('+u"τ"+')]', 0,
                self.ndep-1, 1, self.ndep-1, values=self.ltaus, intslider=True)
        self.zslider.slider.valueChanged.connect(self.updateDepth)
        self.tslider = Slider('Time [index]', 0, self.nt-1, 1, 0, intslider=True)
        if self.nt == 1:
            self.tslider.setDisabled(True)
        self.tslider.slider.valueChanged.connect(self.updateTime)

        self.wslider = Slider('Wavelength [index: value]', 0, self.nw-1, 1, 0,
                values=self.wav, units=u'Å', intslider=True)
        self.wslider.slider.valueChanged.connect(self.updateWave)

        # Stokes button group
        self.labels_stokes = 'IQUV'
        self.bgroup = QWidget()
        self.bgroup_stokes = QButtonGroup()
        layout = QHBoxLayout()
        label_stokes = QLabel()
        layout.addWidget(label_stokes)
        label_stokes.setText('Stokes')
        for ii in range(len(self.labels_stokes)):
            button = QRadioButton(self.labels_stokes[ii])
            if ii == 0: button.setChecked(True)
            self.bgroup_stokes.addButton(button, ii)
            layout.addWidget(button)
            button.clicked.connect(self.updateStokes)
        self.bgroup.setLayout(layout)

        # Add widgets to control panel
        cpanel_layout.addWidget(self.zslider)
        cpanel_layout.addWidget(self.tslider)
        cpanel_layout.addWidget(self.wslider)
        cpanel_layout.addWidget(self.bgroup)
        spacerItem = QSpacerItem(50, 50, QSizePolicy.Minimum,
                QSizePolicy.Expanding)
        cpanel_layout.addItem(spacerItem)

        cpanel = QWidget()
        cpanel.setLayout(cpanel_layout)
        cpanel.setFixedWidth(275)

        # ---- initialise canvas ----
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.invpen = pg.mkPen('r', width=3)
        self.invpen2 = pg.mkPen('b', width=3)

        self.icanvas = pg.GraphicsLayoutWidget()
        self.pcanvas = pg.GraphicsLayoutWidget()
        self.pcanvas.setFixedWidth(600)
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
        'Greens', 'Blues_r', 'Blues_r', 'copper']
        ch_colors = ['w', 'k', 'w', 'k', 'k', 'k', 'w', 'k', 'w']

        self.cwimages = []
        for ii in range(len(cols)):
            xtitle = ytitle = None
            if rows[ii] == 2:
                xtitle = 'pixel'
            if cols[ii] == 0:
                ytitle = 'pixel'
            cwimage = CWImage(self.icanvas, row=rows[ii], col=cols[ii],
                    cm_name=cm.get_cmap(cm_names[ii]), ch_color=ch_colors[ii],
                    xtitle=xtitle, ytitle=ytitle, parent=self)
            self.cwimages.append(cwimage)

        for ii in range(len(cols)-1):
            self.linkviews(self.cwimages[0].box, self.cwimages[ii+1].box)

        # Fill plot canvas
        rows = [0, 0, 1, 1, 2, 2]
        cols = [0, 1] * 3
        xtitles_mod = ['log('+u"τ"+')'] * 2
        if self.plot_iwav:
            self.wunit = 'index'
        else:
            self.wunit = u'Å'
        xtitles_obs = ['wavelength [{0}]'.format(self.wunit)] * 4
        xtitles = xtitles_mod + xtitles_obs
        ytitles_mod = ['T [kK]', 'v [km/s]']
        ytitles_obs = [i+j+k for i,j,k in zip(['Stokes ']*4, self.labels_stokes,[' (scaled)'] * 4)]
        ytitles = ytitles_mod + ytitles_obs
        self.cwplots = []
        for ii in range(len(cols)):
            cwplot = CWPlot(self.pcanvas, row=rows[ii], col=cols[ii],
                    xGrid=True, yGrid=True, addMarker=True, plotwidth=275,
                    xtitle=xtitles[ii], ytitle=ytitles[ii])
            self.cwplots.append(cwplot)

        # Link plot panel views
        self.cwplots[1].box.setXLink(self.cwplots[0].box)
        for ii in range(3):
            self.cwplots[ii+3].box.setXLink(self.cwplots[2].box)

        self.updateWMarker()
        self.updateTauMarker()

        # ----- initialise menubar ----
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('File')
        viewmenu = menubar.addMenu('View')

        exitButton = QAction('Quit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.triggered.connect(qApp.quit)
        filemenu.addAction(exitButton)

        wincButton = QAction('Wavelength up', self)
        wincButton.setShortcut('Shift+S')
        wincButton.triggered.connect(self.incWave)
        viewmenu.addAction(wincButton)
        wdecButton = QAction('Wavelength down', self)
        wdecButton.setShortcut('Shift+A')
        wdecButton.triggered.connect(self.decWave)
        viewmenu.addAction(wdecButton)

        tincButton = QAction('Time up', self)
        tincButton.setShortcut('Shift+F')
        tincButton.triggered.connect(self.incTime)
        viewmenu.addAction(tincButton)
        tdecButton = QAction('Time down', self)
        tdecButton.setShortcut('Shift+B')
        tdecButton.triggered.connect(self.decTime)
        viewmenu.addAction(tdecButton)

        dincButton = QAction('Depth up', self)
        dincButton.setShortcut('Shift+X')
        dincButton.triggered.connect(self.incDepth)
        viewmenu.addAction(dincButton)
        ddecButton = QAction('Depth down', self)
        ddecButton.setShortcut('Shift+Z')
        ddecButton.triggered.connect(self.decDepth)
        viewmenu.addAction(ddecButton)

        fnameButton = QAction('Show filenames', self)
        fnameButton.setShortcut('Ctrl+F')
        fnameButton.triggered.connect(self.showFname)
        viewmenu.addAction(fnameButton)

        # ---- initialise statusbar ----
        self.status = self.statusBar()

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
        self.ltaus = self.m.ltau[0,self.ny//2,self.nx//2,:]
        self.ndep = self.m.ndep

        self.m.azi *= 180./np.pi
        self.m.vturb *= 1.e-5  # in km/s
        self.m.vlos *= 1.e-5
        self.m.temp /= 1.e3 # in kK
        self.m.Bln /= 1.e3 # in kG
        self.m.Bho /= 1.e3 # in kG

        self.minmax_vlos = np.zeros((2, self.m.ndep), dtype='float64')
        self.minmax_vlos[0,:] = np.min(self.m.vlos, axis=(0,1,2))
        self.minmax_vlos[1,:] = np.max(self.m.vlos, axis=(0,1,2))
        self.minmax_vlos_all = (self.minmax_vlos[0].min(), self.minmax_vlos[1].max())
        self.absmax_vlos = np.abs(self.m.vlos).max()
        self.lut_vlos = mplcm_to_pglut(cmap_truncate(cm.get_cmap('bwr'),
            absmax=self.absmax_vlos, minmax=(self.m.vlos[:,:,:,self.itau].min(),
                self.m.vlos[:,:,:,self.itau].max()) ) )

        self.minmax_Bln = np.zeros((2, self.m.ndep), dtype='float64')
        self.minmax_Bln[0,:] = np.min(self.m.Bln, axis=(0,1,2))
        self.minmax_Bln[1,:] = np.max(self.m.Bln, axis=(0,1,2))
        self.minmax_Bln_all = (self.minmax_Bln[0].min(), self.minmax_Bln[1].max())
        self.absmax_Bln = np.abs(self.m.Bln).max()
        self.lut_Bln = mplcm_to_pglut(cmap_truncate(cm.get_cmap('RdGy_r'),
            absmax=self.absmax_Bln, minmax=(self.m.Bln[:,:,:,self.itau].min(),
                self.m.Bln[:,:,:,self.itau].max()) ) )
        print("initModel: Model has dimensions (nx,ny)=({0},{1})".format(self.nx,
            self.ny))

    def initSynth(self):
        self.s = sp.profile(self.fname_synth)
        self.synprof = self.s.dat[:,:,:,self.wsel,:]
        self.nw = self.wsel.size
        self.ww = 0
        self.istokes = 0

    def initObs(self):
        self.o = sp.profile(self.fname_obs)
        self.wsel = np.where(self.o.dat[0,self.o.ny//2,self.o.nx//2,:,0] > 0)[0]
        self.wav = self.o.wav[self.wsel]
        self.plot_iwav = np.diff(self.wav).max() > 50.
        if self.plot_iwav:
            self.plot_wav = np.arange(self.wsel.size)
        else:
            self.plot_wav = self.wav
        self.obsprof = self.o.dat[:,:,:,self.wsel,:]

    def getChi2(self):
        self.wts = np.zeros(self.obsprof.shape)
        self.wts[:,:,:] = self.o.weights[self.wsel,:]
        self.chi2_stokes = np.sum(((self.obsprof - self.synprof)/self.wts)**2,
                axis=3) / self.nw
        self.chi2 = np.sum(self.chi2_stokes, axis=3) / self.o.ns

    def vminmaxImage(self):
        min_syn = np.min(self.s.dat[:,:,:,self.wsel,:], axis=(0,1,2,3))
        max_syn = np.max(self.s.dat[:,:,:,self.wsel,:], axis=(0,1,2,3))
        min_obs = np.min(self.o.dat[:,:,:,self.wsel,:], axis=(0,1,2,3))
        max_obs = np.max(self.o.dat[:,:,:,self.wsel,:], axis=(0,1,2,3))
        self.vminmax = []
        for ii in range(4):
            self.vminmax.append((np.minimum(min_syn[ii], min_obs[ii]),
                np.maximum(max_syn[ii], max_obs[ii])))

    def drawModel(self):
        self.cwimages[0].img.setImage(self.m.temp[self.tt,:,:,self.itau])
        self.cwimages[1].img.setImage(self.m.vlos[self.tt,:,:,self.itau],
                levels=self.minmax_vlos[:,self.itau], lut=self.lut_vlos)
        self.cwimages[2].img.setImage(self.m.vturb[self.tt,:,:,self.itau])
        self.cwimages[3].img.setImage(self.m.Bln[self.tt,:,:,self.itau],
                levels=self.minmax_Bln[:,self.itau], lut=self.lut_Bln)
        self.cwimages[4].img.setImage(self.m.Bho[self.tt,:,:,self.itau])
        self.cwimages[5].img.setImage(self.m.azi[self.tt,:,:,self.itau])

    def plotModel(self):
        self.cwplots[0].invplot.setData(self.ltaus, self.m.temp[self.tt,self.yy,self.xx,:],
                pen=self.invpen)
        self.cwplots[1].invplot.setData(self.ltaus, self.m.vlos[self.tt,self.yy,self.xx,:],
                pen=self.invpen)
        self.cwplots[1].invplot2.setData(self.ltaus, self.m.vturb[self.tt,self.yy,self.xx,:],
                pen=self.invpen2)

    def drawSynth(self):
        self.cwimages[7].img.setImage(self.synprof[self.tt,:,:,self.ww,self.istokes],
                levels=self.vminmax[self.istokes])

    def plotSynth(self):
        for ii in range(4):
            self.cwplots[ii+2].invplot.setData(self.plot_wav,
                    self.synprof[self.tt,self.yy,self.xx,:,ii], pen=self.invpen)

    def drawObs(self):
        self.cwimages[6].img.setImage(self.obsprof[self.tt,:,:,self.ww,self.istokes],
                levels=self.vminmax[self.istokes])
        self.cwimages[8].img.setImage(self.chi2[self.tt,:,:])

    def plotObs(self):
        for ii in range(4):
            self.cwplots[ii+2].obsplot.setData(self.plot_wav,
                    self.obsprof[self.tt,self.yy,self.xx,:,ii], symbol='o',
                    symbolPen='k')

    def linkviews(self, anchorview, view):
        view.setXLink(anchorview)
        view.setYLink(anchorview)

    def getFileName(self, typedict=None):
        inam = 'getFileName'
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self, 
            "Please select the input {0} file".format(typedict['name']), self.cwd, 
            "STiC {0} file ({1})".format(typedict['fullname'],
                typedict['filter']), options=options)
        if filename:
            print("{0}: opening {1} file {2}".format(inam, typedict['fullname'],
                filename))
            dirname = os.path.dirname(filename)
            if self.cwd != dirname: self.cwd = dirname
            return filename
        else:
            print("{0} [error]: {1} file required to launch " \
                    "STiCViewer".format(inam, typedict['fullname']))
            sys.exit()

    def updateDepth(self):
        self.itau = self.zslider.sval 
        self.lut_vlos = mplcm_to_pglut(cmap_truncate(cm.get_cmap('bwr'),
            absmax=self.absmax_vlos, minmax=(self.m.vlos[:,:,:,self.itau].min(),
                self.m.vlos[:,:,:,self.itau].max()) ) )
        self.lut_Bln = mplcm_to_pglut(cmap_truncate(cm.get_cmap('RdGy_r'),
            absmax=self.absmax_Bln, minmax=(self.m.Bln[:,:,:,self.itau].min(),
                self.m.Bln[:,:,:,self.itau].max()) ) )
        self.drawModel()
        self.updateTauMarker()
        self.updateStatus()

    def updateTime(self):
        self.tt = self.tslider.sval
        self.drawModel()
        self.drawSynth()
        self.drawObs()
        self.plotModel()
        self.updateStatus()

    def updateWave(self):
        self.ww = self.wslider.sval
        self.drawSynth()
        self.drawObs()
        self.updateWMarker()
        self.updateStatus()

    def updateWMarker(self):
        for ii in range(4):
            self.cwplots[ii+2].line.setPos(self.plot_wav[self.ww])

    def updateTauMarker(self):
        for ii in range(2):
            self.cwplots[ii].line.setPos(self.ltaus[self.itau])

    def updateCrosshairs(self):
        self.updateStatus()
        for ii in range(len(self.cwimages)):
            self.cwimages[ii].vLine.setPos(self.xx+0.5) # +0.5: place mid-pixel
            self.cwimages[ii].hLine.setPos(self.yy+0.5)

    def updateStokes(self):
        self.istokes = self.bgroup_stokes.checkedId()
        self.drawObs()
        self.drawSynth()
        self.updateStatus()

    def updateStatus(self):
        coords = 'Position: (x,y)=({0:>3},{1:>3})'.format(self.xx, self.yy)
        model = 'Model: T[kK]={0:>6.2f}, vlos[km/s]={1:>6.2f}, vturb[km/s]={2:>6.2f}, Bln[kG]={3:>6.2f}, Bho[kG]={4:>6.2f}, azi[deg]={5:>5.1f})'.\
                format(self.m.temp[self.tt, self.yy, self.xx, self.itau],
                        self.m.vlos[self.tt, self.yy, self.xx, self.itau],
                        self.m.vturb[self.tt, self.yy, self.xx, self.itau],
                        self.m.Bln[self.tt, self.yy, self.xx, self.itau],
                        self.m.Bho[self.tt, self.yy, self.xx, self.itau],
                        self.m.azi[self.tt, self.yy, self.xx, self.itau])
        profs = 'Profile: Iobs={0:>6.3f}, Isyn={1:>6.3f}, Chi2={2:>5.2f} [(I, Q, U, V)=({3:>5.2f},{4:>5.2f},{5:>5.2f},{6:>5.2f})]'.\
                format(self.obsprof[self.tt, self.yy, self.xx, self.ww, self.istokes],
                    self.synprof[self.tt, self.yy, self.xx, self.ww, self.istokes],
                    self.chi2[self.tt, self.yy, self.xx],
                    self.chi2_stokes[self.tt, self.yy, self.xx, 0],
                    self.chi2_stokes[self.tt, self.yy, self.xx, 1],
                    self.chi2_stokes[self.tt, self.yy, self.xx, 2],
                    self.chi2_stokes[self.tt, self.yy, self.xx, 3])
        self.status.showMessage(coords+' | '+model+' | '+profs)

    def showFname(self):
        filenames = 'Observed: {0} | Synthetic: {1} | Model: {2}'.\
                format(os.path.basename(self.fname_obs),
                        os.path.basename(self.fname_synth),
                        os.path.basename(self.fname_atmos))
        self.status.showMessage(filenames)

    def incWave(self):
        self.ww += 1
        if (self.ww >= self.nw): self.ww = 0
        self.changeWave()

    def decWave(self):
        self.ww -= 1
        if (self.ww < 0): self.ww = self.nw-1
        self.changeWave()

    def changeWave(self):
        self.wslider.setValue(self.ww)
        self.drawSynth()
        self.drawObs()
        self.updateWMarker()
        self.updateStatus()

    def incTime(self):
        self.tt += 1
        if (self.tt >= self.nt): self.tt = 0
        self.changeTime()

    def decTime(self):
        self.tt -= 1
        if (self.tt < 0): self.tt = self.nt-1
        self.changeTime()

    def changeTime(self):
        self.tslider.setValue(self.tt)
        self.drawModel()
        self.drawSynth()
        self.drawObs()
        self.plotModel()
        self.plotSynth()
        self.plotObs()
        self.updateWMarker()
        self.updateStatus()

    def incDepth(self):
        self.itau += 1
        if (self.itau >= self.ndep): self.itau = 0
        self.changeDepth()

    def decDepth(self):
        self.itau -= 1
        if (self.itau < 0): self.itau = self.ndep-1
        self.changeDepth()

    def changeDepth(self):
        self.zslider.setValue(self.itau)
        self.drawModel()
        self.drawSynth()
        self.drawObs()
        self.plotModel()
        self.plotSynth()
        self.plotObs()
        self.updateWMarker()
        self.updateStatus()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()

    sys.exit(app.exec_())
