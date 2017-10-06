import os
import sys
import traceback
import urllib
import urllib.request
from contextlib import suppress

import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, qApp, QMessageBox, QGridLayout, QWidget, \
    QVBoxLayout, QFrame, QLabel, QLineEdit, QFileDialog, QDesktopWidget, QTextBrowser

from controllers.data_control import update_user_data, load_user_data, extract_7z
from controllers.dolphin_control import get_dolphin_link, get_dolphin_html, get_dolphin_changelog


class DolphinUpdate(QMainWindow):

    APP_TITLE = 'DolphinUpdate'
    DOWNLOAD_PATH = os.path.join(os.getenv('APPDATA'), 'DolphinUpdate/')

    def __init__(self):
        super().__init__()
        sys.excepthook = self._displayError

        self.statusBar = self.statusBar()
        self.check = QPixmap("res/check.png")
        self.cancel = QPixmap("res/cancel.png")

        self.init_ui()
        self.init_window()

        self.init_user_data()

        self.setGeometry(500, 500, 500, 465)
        center(self)
        self.setWindowTitle(self.APP_TITLE)
        self.setWindowIcon(QIcon('res/rabbit.png'))

        self.show()

    # PyQt Error Handling
    def _displayError(self, etype, evalue, etraceback):
        tb = ''.join(traceback.format_exception(etype, evalue, etraceback))
        QMessageBox.critical(self, "FATAL ERROR", "An unexpected error occurred:\n%s\n\n%s" % (evalue, tb))

    def init_ui(self):
        """create the UI elements in the main window"""
        self.statusBar.showMessage('Ready')

        main = QWidget()
        self.setCentralWidget(main)

        self.dolphin_dir = QLineEdit(main)
        self.dolphin_dir.setPlaceholderText("Please Select a Dolphin Directory")
        self.dolphin_dir.setReadOnly(True)

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
        changelog_frame.setContentsMargins(0, 20, -7, 0)

        grid = QGridLayout()
        main.setLayout(grid)

        self.dolphin_dir_status = QLabel(main)
        self.dolphin_dir_status.setPixmap(self.cancel)
        self.version_status = QLabel(main)
        self.version_status.setPixmap(self.cancel)
        self.current_status = QLabel(main)
        self.current_status.setPixmap(QPixmap("res/info.png"))

        grid.addWidget(self.dolphin_dir_status, 0, 0, Qt.AlignCenter)
        grid.addWidget(QLabel('Dolphin Directory:'), 0, 2)
        grid.addWidget(self.dolphin_dir, 0, 3)

        grid.addWidget(self.version_status, 1, 0, Qt.AlignCenter)
        grid.addWidget(QLabel('Your Version:'), 1, 2)
        grid.addWidget(self.version, 1, 3)

        grid.addWidget(self.current_status, 2, 0, Qt.AlignCenter)
        grid.addWidget(QLabel('Current Version:'), 2, 2)
        grid.addWidget(self.current, 2, 3)

        grid.addWidget(changelog_frame, 4, 0, 1, 4)

        grid.setSpacing(10)
        grid.setVerticalSpacing(2)
        grid.setRowStretch(4, 1)

    def init_window(self):
        self.update_thread = UpdateThread()
        self.update_thread.current.connect(self.update_current)
        self.update_thread.changelog.connect(self.update_changelog)
        self.update_thread.error.connect(self.show_warning)
        self.update_thread.start()

        self.download_thread = DownloadThread()
        self.download_thread.status.connect(self.update_version)
        self.download_thread.error.connect(self.show_warning)

        open_action = QAction(QIcon('res/open.png'), '&Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Select Dolphin Folder')
        open_action.triggered.connect(self.select_dolphin_folder)

        update_action = QAction(QIcon('res/synchronize.png'), '&Refresh', self)
        update_action.setStatusTip('Refresh Current Version')
        update_action.triggered.connect(self.retrieve_current)

        download_action = QAction(QIcon('res/download.png'), '&Download', self)
        download_action.setStatusTip('Download Newest Version')
        download_action.triggered.connect(self.download_new)

        clear_action = QAction(QIcon('res/delete.png'), '&Clear Version', self)
        clear_action.setStatusTip('Reset Your Version')
        clear_action.triggered.connect(self.clear_version)

        exit_action = QAction(QIcon('res/exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(qApp.quit)

        launch_dolphin_action = QAction(QIcon('res/dolphin.png'), '&Launch Dolphin', self)
        launch_dolphin_action.setShortcut('Ctrl+D')
        launch_dolphin_action.setStatusTip('Launch Dolphin')
        launch_dolphin_action.triggered.connect(self.launch_dolphin)

        file_menu = self.menuBar().addMenu('&File')
        file_menu.addAction(open_action)
        file_menu.addAction(update_action)
        file_menu.addAction(clear_action)
        file_menu.addAction(launch_dolphin_action)
        file_menu.addAction(exit_action)

        toolbar = self.addToolBar('Toolbar')
        toolbar.addAction(open_action)
        toolbar.addAction(update_action)
        toolbar.addAction(download_action)
        toolbar.addSeparator()
        toolbar.addAction(launch_dolphin_action)

    def launch_dolphin(self):
        dolphin_dir = self.dolphin_dir.text()
        if not dolphin_dir:
            self.show_warning('Please select a dolphin folder.')
            return

        dolphin_path = os.path.join(dolphin_dir, 'Dolphin.exe')
        if not os.path.isfile(dolphin_path):
            self.show_warning('Could not find "Dolphin.exe".')
            return

        subprocess.Popen(dolphin_path, cwd=dolphin_dir)
        qApp.quit()

    def update_version(self, message):
        if message == 'finished':
            self.version.setText(self.version.placeholderText())
            self.version.setPlaceholderText("Installation Status Unknown")
            self.version_status.setPixmap(self.check)
            update_user_data(self.dolphin_dir.text(), self.version.text())

        else:
            self.version.setPlaceholderText(message)

    def download_new(self):
        dolphin_dir = self.dolphin_dir.text()
        version = self.version.text()

        if self.current.text() == version:
            self.show_warning('You already have the most recent version.')
            return
        elif not os.path.isdir(dolphin_dir):
            self.show_warning('Uh-oh', 'Your dolphin folder path is invalid.')
            self.dolphin_dir_status.setPixmap(QPixmap("res/cancel.png"))
            return

        if not self.download_thread.isRunning():
            if dir == 'Please Select a Dolphin Directory':
                self.show_warning('Please select a dolphin folder.')

            self.version.setText('')
            self.download_thread.update(dolphin_dir, version)
            self.download_thread.start()

    def update_changelog(self, message):
        self.changelog.setText(message)

    def show_warning(self, message):
        QMessageBox.warning(self, 'Uh-oh', message, QMessageBox.Ok)

    def clear_version(self):
        reply = QMessageBox.question(self, 'Clear', "Are you sure you want to reset your version?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.version.setText('')
            self.version_status.setPixmap(self.cancel)
            update_user_data(self.dolphin_dir.text(), '')

    def retrieve_current(self):
        if ~self.update_thread.isRunning():
            self.current.setText('')
            self.update_thread.start()

    def update_current(self, current):
        self.current.setText(current)
        if self.version.text() == self.current.text():
            self.version_status.setPixmap(self.check)
        else:
            self.version_status.setPixmap(self.cancel)

    def select_dolphin_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, 'Select Dolphin Directory'))

        if folder:
            self.dolphin_dir.setText(folder)
            self.dolphin_dir_status.setPixmap(QPixmap("res/check.png"))
            version = self.version.text()
            update_user_data(folder, version)


    def init_user_data(self):
        """initialize the dolphin path"""
        try:
            path, version = load_user_data()
            if path:
                self.dolphin_dir.setText(path)
                if os.path.isdir(path):
                    self.dolphin_dir_status.setPixmap(self.check)
            if version:
                self.version.setText(version)

        except:
            update_user_data('', '')

    # PyQt closeEvent called on exit
    def closeEvent(self, event):
        if self.download_thread.isRunning() or self.update_thread.isRunning():
            reply = QMessageBox.question(self, 'Exit', "Are you sure to quit?", QMessageBox.Yes |
                                         QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.No:
                event.ignore()
                return
            else:
                self.download_thread.wait()
                self.update_thread.wait()

        event.accept()


class UpdateThread(QThread):
    current = pyqtSignal(str)
    changelog = pyqtSignal(str)
    error = pyqtSignal(str)

    def __del__(self):
        self.wait()

    def run(self, *args):
        try:
            dolphin_html = get_dolphin_html()
        except:
            self.error.emit('No connection to dolphin-emu.org, try again later.')
            return

        try:
            link = get_dolphin_link(dolphin_html)
            changelog = get_dolphin_changelog(dolphin_html)
            self.current.emit(os.path.basename(link))
            self.changelog.emit(changelog)
        except:
            self.error.emit('Error parsing dolphin-emu.org, please contact the developer.')


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
        self.status.emit('Getting newest version...')
        try:
            link = get_dolphin_link()
        except:
            self.error.emit('Newest version not detected, please check your internet connection.')
            return

        file_name = os.path.basename(link)
        zip_file = os.path.join(DolphinUpdate.DOWNLOAD_PATH, file_name)
        to_directory = os.path.dirname(self.dir)

        try:
            self.status.emit('Downloading...')
            urllib.request.urlretrieve(link, zip_file)
            self.status.emit('Downloaded. Extracting...')

            if not os.path.isfile('res/7za.exe'):
                self.error.emit('Update failed: Please install 7-Zip')
                self.status.emit('Extraction Failed')
                return

            os.rename(self.dir, os.path.join(to_directory, 'Dolphin-x64'))
            extract_7z(zip_file, to_directory)

            self.status.emit(file_name)
            self.status.emit('finished')

        except Exception as error:
            self.error.emit('Update Failed. %s' % error)
            self.status.emit('Update Failed.')
        finally:
            with suppress(FileNotFoundError):
                os.remove(zip_file)
                os.rename(os.path.join(to_directory, 'Dolphin-x64'), self.dir)


def center(w):
    qr = w.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    w.move(qr.topLeft())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DolphinUpdate()
    sys.exit(app.exec_())
