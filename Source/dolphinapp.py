import os
import pickle
import subprocess
import sys
import traceback
import urllib
import urllib.request

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, qApp, QMessageBox, QGridLayout, QWidget, \
    QVBoxLayout, QFrame, QLabel, QLineEdit, QFileDialog, QDesktopWidget, QTextBrowser
from bs4 import BeautifulSoup


class DolphinUpdate(QMainWindow):

    APP_TITLE = 'DolphinUpdate'
    DOWNLOAD_PATH = os.path.join(os.getenv('APPDATA'), 'DolphinUpdate/')
    USER_DATA_PATH = os.path.join(os.getenv('APPDATA'), 'DolphinUpdate/user.data')

    def __init__(self):

        super().__init__()
        sys.excepthook = self._displayError

        self.statusBar = self.statusBar()
        self.check = QPixmap("res/check.png")
        self.cancel = QPixmap("res/cancel.png")

        self.initWindow()
        self.initUI()
        self.loadData()

        self.setGeometry(500, 500, 500, 450)
        center(self)
        self.setWindowTitle(self.APP_TITLE)
        self.setWindowIcon(QIcon('res/rabbit.png'))

        self.show()
        self.raise_()

    # PyQt Error Handling
    def _displayError(self, etype, evalue, etraceback):
        tb = ''.join(traceback.format_exception(etype, evalue, etraceback))
        QMessageBox.critical(self, "FATAL ERROR", "An unexpected error occurred:\n%s\n\n%s" % (evalue, tb))

    def initUI(self):
        """create the UI elements in the main window"""
        self.statusBar.showMessage('Ready')

        main = QWidget()
        self.setCentralWidget(main)

        self.dolphindir = QLineEdit(main)
        self.dolphindir.setPlaceholderText("Please Select a Dolphin Directory")
        self.dolphindir.setReadOnly(True)

        self.version = QLineEdit(main)
        self.version.setPlaceholderText("Installation Status Unknown")
        self.version.setReadOnly(True)

        self.current = QLineEdit(main)
        self.current.setPlaceholderText("Loading Current Version...")
        self.current.setReadOnly(True)
        
        changelog_frame = QFrame(main)
        changelog_vbox = QVBoxLayout(changelog_frame)
        self.changelog = QTextBrowser(main)
        self.changelog.setPlaceholderText("Loading Changelog...")
        self.changelog.setReadOnly(True)
        changelog_vbox.addWidget(QLabel('Changelog:'))
        changelog_vbox.addWidget(self.changelog)
         
        self.grid = QGridLayout()
        main.setLayout(self.grid)

        self.dirstatus = QLabel(main)
        self.dirstatus.setPixmap(self.cancel)
        self.versionstatus = QLabel(main)
        self.versionstatus.setPixmap(self.cancel)
        self.currentStatus = QLabel(main)
        self.currentStatus.setPixmap(QPixmap("res/info.png"))


        self.grid.addWidget(self.dirstatus, 0, 0)
        self.grid.addWidget(QLabel('Dolphin Directory:'), 0, 2)
        self.grid.addWidget(self.dolphindir, 0, 3)

        self.grid.addWidget(self.versionstatus, 1, 0)
        self.grid.addWidget(QLabel('Your Version:'), 1, 2)
        self.grid.addWidget(self.version, 1, 3)

        self.grid.addWidget(self.currentStatus, 2, 0)
        self.grid.addWidget(QLabel('Current Version:'), 2, 2)
        self.grid.addWidget(self.current, 2, 3)

        self.grid.addWidget(changelog_frame, 4, 0, 1, 4)

        self.grid.setSpacing(10)
        self.grid.setVerticalSpacing(2)
        self.grid.setRowStretch(4, 1)

    def initWindow(self):

        openAction = QAction(QIcon('res/open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Select Dolphin Folder')
        openAction.triggered.connect(self.selectDolphinFolder)

        self.updateThread = thread(self._retrieveCurrent)
        self.updateThread.finished.connect(self.retrieveCurrentFinished)
        self.updateThread.changelogtext.connect(self.updateChangelog)

        self.updateThread.start()

        self.downloadThread = DownloadThread()
        self.downloadThread.status.connect(self.updateVersion)
        self.downloadThread.error.connect(self.handleDownloadError)

        updateAction = QAction(QIcon('res/synchronize.png'), '&Refresh', self)
        updateAction.setStatusTip('Get Current Version')
        updateAction.triggered.connect(self.retrieveCurrent)

        downloadAction = QAction(QIcon('res/download.png'), '&Download', self)
        downloadAction.setStatusTip('Download Newest Version')
        downloadAction.triggered.connect(self.downloadNew)

        clearAction = QAction(QIcon('res/delete.png'), '&Clear Version', self)
        clearAction.setStatusTip('Reset Your Version')
        clearAction.triggered.connect(self.clearVersion)

        exitAction = QAction(QIcon('res/exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(updateAction)
        fileMenu.addAction(clearAction)
        fileMenu.addAction(exitAction)

        toolbar = self.addToolBar('Toolbar')
        toolbar.addAction(openAction)
        toolbar.addAction(updateAction)
        toolbar.addAction(downloadAction)

    def updateVersion(self, message):
        if message == 'finished':
            self.versionstatus.setPixmap(self.check)
            with open(self.USER_DATA_PATH, 'wb') as file:
                data = {'path': self.dolphindir.text(), 'version': self.version.text()}
                pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)

        else:
            self.version.setText(message)

    def updateChangelog(self, message):
            self.changelog.setText(message)

    def downloadNew(self):
        dir = self.dolphindir.text()
        version = self.version.text()

        if self.current.text() == version:
            QMessageBox.warning(self, 'Uh-oh', 'You already have the most recent version.', QMessageBox.Ok)
            return
        elif not os.path.isdir(self.dolphindir.text()):
            QMessageBox.warning(self, 'Uh-oh', 'Your dolphin folder path is invalid.', QMessageBox.Ok)
            self.dirstatus.setPixmap(QPixmap("res/cancel.png"))
            return

        if not self.downloadThread.isRunning():
            if dir == 'Please Select a Dolphin Directory':
                QMessageBox.warning(self, 'Uh-oh', 'Please select a dolphin folder.', QMessageBox.Ok)

            self.version.setText('Getting newest version...')
            self.downloadThread.update(dir, version)
            self.downloadThread.start()

    def handleDownloadError(self, error):
        QMessageBox.warning(self, 'Uh-oh', error, QMessageBox.Ok)

    def loadData(self):
        """initialize the dolphin path"""
        text_path = self.USER_DATA_PATH
        if os.path.isfile(text_path):
            # Load data (deserialize)
            try:
                with open(text_path, 'rb') as file:
                    data = pickle.load(file)

                path = data['path']
                version = data['version']
                if path:
                    self.dolphindir.setText(path)
                    if os.path.isdir(path):
                        self.dirstatus.setPixmap(self.check)
                if version:
                    self.version.setText(version)


            except:
                with open(text_path, 'wb') as file:
                    data = {'path': '', 'version': ''}
                    pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)

    def clearVersion(self):
        reply = QMessageBox.question(self, 'Clear', "Are you sure you want to reset your version?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.version.setText('Installation Status Unknown')
            self.versionstatus.setPixmap(self.cancel)
            with open(self.USER_DATA_PATH, 'wb') as file:
                data = {'path': self.dolphindir.text(), 'version': ''}
                pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)

    def retrieveCurrent(self):
        self.current.setText('Loading Current Version...')
        if ~self.updateThread.isRunning():
            self.updateThread.start()

    def retrieveCurrentFinished(self):
        if self.version.text() == self.current.text():
            self.versionstatus.setPixmap(self.check)
        else:
            self.versionstatus.setPixmap(self.cancel)

    def _retrieveCurrent(self):
        result = {}
        try:
            url = 'https://dolphin-emu.org/download/'
            response = urllib.request.urlopen(url)
            data = response.read()
            text = data.decode('utf-8')
            soup = BeautifulSoup(text, "html.parser")
            try:
                link = soup.find_all('a', {"class": 'btn always-ltr btn-info win'}, limit=1, href=True)[0]['href']
                self.current.setText(os.path.basename(link))
            except:
                QMessageBox.warning(self, 'Uh-oh', 'Newest version not detected, please contact '
                                                   'the developer.', QMessageBox.Ok)

            try:
                text = ""
                sections = soup.find('table', {"class": 'versions-list dev-versions'})
                for section in sections.find_all('tr',{"class": 'infos'}):
                    version = section.find("td",{"class": "version"}).find("a").get_text()
                    change = section.find("td",{"class": "description"}).get_text()
                    text = text  + version + "\n" + change + "\n\n"

                result["changelog"] = text
            except:
                QMessageBox.warning(self, 'Uh-oh', 'Changelog not detected, please contact '
                                                   'the developer.', QMessageBox.Ok)
        except Exception as error:
            QMessageBox.warning(self, 'Uh-oh', error, QMessageBox.Ok)

        return result

    def selectDolphinFolder(self):
        folder = str(QFileDialog.getExistingDirectory(self, 'Select Dolphin Directory'))

        if folder:
            self.dolphindir.setText(folder)
            self.dirstatus.setPixmap(QPixmap("res/check.png"))
            if self.version.text() != 'Installation Status Unknown':
                version = self.version.text()
            else:
                version = ''

            data = {'path': folder, 'version': version}
            with open(self.USER_DATA_PATH, 'wb') as file:
                pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)

    def closeEvent(self, event):
        if self.downloadThread.isRunning() or self.updateThread.isRunning():
            reply = QMessageBox.question(self, 'Exit', "Are you sure to quit?", QMessageBox.Yes |
                                         QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.No:
                event.ignore()
            else:
                self.downloadThread.wait()
                self.updateThread.wait()

        event.accept()


def center(w):
    qr = w.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    w.move(qr.topLeft())


class thread(QThread):
    finished = pyqtSignal(str)
    changelogtext = pyqtSignal(str)

    def __init__(self, func, *args):
        QThread.__init__(self)
        self.func = func
        self.args = args

    def __del__(self):
        self.wait()

    def run(self, *args):
        result = self.func(*args)

        if "changelog" in result:
            self.changelogtext.emit(result["changelog"])

        self.finished.emit("Finished")


class DownloadThread(QThread):
    status = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, dir='', version=''):
        QThread.__init__(self)
        self.version = version
        self.dir = dir

    def __del__(self):
        self.wait()

    def update(self, dir, version):
        self.version = version
        self.dir = dir

    def run(self):
        """run thread task"""
        try:
            url = 'https://dolphin-emu.org/download/'
            response = urllib.request.urlopen(url)
            data = response.read()
            text = data.decode('utf-8')
            soup = BeautifulSoup(text, "html.parser")
            link = soup.find_all('a', {"class": 'btn always-ltr btn-info win'}, limit=1, href=True)[0]['href']
        except:
            self.error.emit('Newest version not detected, please check your internet connection.')
            return

        file_name = os.path.basename(link)
        file_path = os.path.join(DolphinUpdate.DOWNLOAD_PATH, file_name)

        try:
            self.status.emit('Downloading...')
            urllib.request.urlretrieve(link, file_path)
            self.status.emit('Downloaded. Extracting...')
            path = os.path.dirname(self.dir)

            if not os.path.isfile('res/7za.exe'):
                self.error.emit('Update failed: Please install 7-Zip')
                self.status.emit('Extraction Failed')
                return

            os.rename(self.dir, os.path.join(os.path.dirname(self.dir), 'Dolphin-x64'))
            cmd = ['res\\7za', 'x', '-o%s' % path, '-y', '--', file_path]
            starti = subprocess.STARTUPINFO()
            starti.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.call(cmd, startupinfo=starti,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            stdin=subprocess.PIPE)

            self.status.emit(file_name)
            self.status.emit('finished')

        except Exception as error:
            self.error.emit('Update Failed. %s' % error)
            self.status.emit('Update Failed.')
        finally:
            if os.path.isfile(file_path):
                os.remove(file_path)
            if os.path.isdir(os.path.join(os.path.dirname(self.dir), 'Dolphin-x64')):
                os.rename(os.path.join(os.path.dirname(self.dir), 'Dolphin-x64'), self.dir)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DolphinUpdate()
    sys.exit(app.exec_())
