# STiCViewer
STiCViewer is a graphical user interface written in PyQt5 to visualise output
from the STockholm Inversion Code
([STiC](https://github.com/jaimedelacruz/stic)). 

## Setup
STiCViewer requires Python 3 to run.
In addition, you will need to have the following dependencies
installed:
* PyQt5
* PyQtGraph ([http://www.pyqtgraph.org/](http://www.pyqtgraph.org/))
* sparsetools.py (comes with the STiC distribution)


For convenience one can create an alias to allow calling STiCViewer from
anywhere, e.g. in bash:
```
alias sticviewer='python3 ~/git/sticviewer/sticviewer.py'
```

## Running STiCViewer
There are two ways of running STiCViewer:
* by simply executing the python script without any arguments. This will pop up
  a file search window in which you can select the observed, synthetic and model
  atmosphere files (in that order).
* by providing three arguments to the script, e.g.:
  ```
  sticviewer observed.nc synthetic.nc atmosout.nc
  ```
  This will skip the pop-up file search and load those file directly.

Sample data for preview purposes are provided in the `sample` directory.
