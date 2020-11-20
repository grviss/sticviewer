# STiCViewer
`STiCViewer` is a graphical user interface written in PyQt5 to visualise output
from the STockholm Inversion Code
([STiC](https://github.com/jaimedelacruz/stic)). 

## Setup
Clone the repository and make sure you have the following dependencies
installed:
* PyQt5
* PyQtGraph ([http://www.pyqtgraph.org/](http://www.pyqtgraph.org/))
* sparsetools (comes with the STiC distribution)

STiCViewer requires Python 3 to run.

For convenience one can create an alias to allow calling STiCViewer from
anywhere, e.g. in bash:
```
alias sticviewer='python ~/git/sticviewer/sticviewer.py'
```
