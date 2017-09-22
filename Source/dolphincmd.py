"""command line for dolphin update"""

#
# Imports
#
import argparse
import os
import pickle
import subprocess
import sys
import urllib
import urllib.request

from bs4 import BeautifulSoup


class DolphinCmd:
    """script for getting dolphin updates"""

    DOWNLOAD_PATH = os.path.join(os.getenv('APPDATA'), 'DolphinUpdate/')
    USER_DATA_PATH = os.path.join(os.getenv('APPDATA'), 'DolphinUpdate/user.data')

    def __init__(self, args=None):
        """Perform argument processing and other setup"""
        self.args = args
        self.path = ''
        self.version = ''
        self._loadData()

    def get_cmdline_options(self):
        """Read commandline options"""
        parser = argparse.ArgumentParser()
        parser.add_argument('-r', '--retrieve', dest='retrieve', action='store_true',
                            help='retrieve the current version from dolphin-emu.org')
        parser.add_argument('-i', '--info', dest='info', action='store_true',
                            help='retrieve your dolphin directory and version')
        parser.add_argument('-c', '--clear-version', dest='clear', action='store_true',
                            help='clear your dolphin version')
        parser.add_argument('-f', '--set-folder', dest='folder', help='set your dolphin directory')
        parser.add_argument('-d', '--download', dest='download', action='store_true', help='set your dolphin directory')
        options = parser.parse_args(self.args)

        # Return the argument values
        return options

    def run(self):
        opt = self.get_cmdline_options()
        if opt.info or not self.args:
            path = self.path
            version = self.version
            print('Dolphin Directory: ' + (path if path else 'Unkown'))
            print('Dolphin Version: ' + (version if version else 'Unkown'))
        if opt.retrieve:
            self._retrieveCurrent()
        if opt.clear:
            self._clearVersion()
        if opt.folder:
            self._setDolphinFolder(opt.folder)
        if opt.download:
            self._downloadNew()

    #
    # Private Methods
    #

    def _downloadNew(self):
        dir = self.path
        version = self.version

        print('Getting newest version...')
        link = self._retrieveCurrent()
        current = os.path.basename(link)

        if os.path.basename(link) == version:
            print('You already have the most recent version.')
            return
        elif not os.path.isdir(self.path):
            print('Your dolphin folder path is invalid.')
            return

        file_name = os.path.basename(link)
        file_path = os.path.join(self.DOWNLOAD_PATH, file_name)

        try:
            print('Downloading...')
            urllib.request.urlretrieve(link, file_path)
            print('Downloaded. Extracting...')

            path = os.path.dirname(dir)

            if not os.path.isfile('res/7za.exe'):
                print('Update failed: Please install 7-Zip')
                return

            os.rename(dir, os.path.join(os.path.dirname(dir), 'Dolphin-x64'))
            cmd = ['res\\7za', 'x', '-o%s' % path, '-y', '--', file_path]
            starti = subprocess.STARTUPINFO()
            starti.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.call(cmd, startupinfo=starti,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            stdin=subprocess.PIPE)

            print('Update successful.')
            self.version = current
            with open(self.USER_DATA_PATH, 'wb') as file:
                data = {'path': self.path, 'version': self.version}
                pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)

        except Exception as error:
            print('Update Failed. %s' % error)
        finally:
            if os.path.isfile(file_path):
                os.remove(file_path)
            if os.path.isdir(os.path.join(os.path.dirname(dir), 'Dolphin-x64')):
                os.rename(os.path.join(os.path.dirname(dir), 'Dolphin-x64'), dir)

    def _setDolphinFolder(self, folder):
        if os.path.isdir(folder):
            self.path = folder
            data = {'path': folder, 'version': self.version}
            with open(self.USER_DATA_PATH, 'wb') as file:
                pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)
            print('Dolphin Directory: ' + folder)
        else:
            print('Directory not found.')

    def _retrieveCurrent(self):
        """retrieve the current version"""
        try:
            url = 'https://dolphin-emu.org/download/'
            response = urllib.request.urlopen(url)
            data = response.read()
            text = data.decode('utf-8')
            soup = BeautifulSoup(text, "html.parser")
            try:
                link = soup.find_all('a', {"class": 'btn always-ltr btn-info win'}, limit=1, href=True)[0]['href']
                print('Newest Version: ' + os.path.basename(link))
                return link
            except:
                print('Newest version not detected, please contact the developer.')
        except Exception as error:
            print(error)

    def _clearVersion(self):
        """clear out your current version"""
        self.version = ''
        with open(self.USER_DATA_PATH, 'wb') as file:
            data = {'path': self.path, 'version': ''}
            pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)
        print('Version cleared.')

    def _loadData(self):
        """initialize the dolphin path"""
        text_path = self.USER_DATA_PATH
        if os.path.isfile(text_path):
            # Load data (deserialize)
            try:
                with open(text_path, 'rb') as file:
                    data = pickle.load(file)
                self.path = data['path']
                self.version = data['version']
            except:
                with open(text_path, 'wb') as file:
                    data = {'path': '', 'version': ''}
                    pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)

def launch_new_instance(args):
    """run the script with args"""
    try:
        script = DolphinCmd(args)
        script.run()

    except KeyboardInterrupt:
        print("Shutdown requested...exiting")

if __name__ == "__main__":
    launch_new_instance(sys.argv[1:])
