"""Command line for dolphin update"""

import argparse
import os
import pickle
import sys
import urllib
import urllib.request
from contextlib import suppress

from Source.controllers.data_control import extract_7z, update_user_data, load_user_data
from Source.controllers.dolphin_control import get_dolphin_link


class DolphinCmd:
    """script for getting dolphin updates"""

    DOWNLOAD_PATH = os.path.join(os.getenv('APPDATA'), 'DolphinUpdate/')

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
        print('Getting newest version...')
        link = self._retrieveCurrent()
        current = os.path.basename(link)

        if os.path.basename(link) == self.version:
            print('You already have the most recent version.')
            return
        elif not os.path.isdir(self.path):
            print('Your dolphin folder path is invalid.')
            return

        file_name = os.path.basename(link)
        zip_file = os.path.join(self.DOWNLOAD_PATH, file_name)
        to_directory = os.path.dirname(self.path)

        try:
            print('Downloading...')
            urllib.request.urlretrieve(link, zip_file)
            print('Downloaded. Extracting...')

            if not os.path.isfile('res/7za.exe'):
                print('Update failed: Please install 7-Zip')
                return

            os.rename(self.path, os.path.join(to_directory, 'Dolphin-x64'))
            extract_7z(zip_file, to_directory)

            print('Update successful.')
            self.version = current
            update_user_data(self.path, self.version)

        except Exception as error:
            print('Update Failed. %s' % error)
        finally:
            with suppress(FileNotFoundError):
                os.remove(zip_file)
                os.rename(os.path.join(to_directory, 'Dolphin-x64'), self.path)

    def _setDolphinFolder(self, folder):
        if os.path.isdir(folder):
            self.path = folder
            update_user_data(folder, self.version)

            print('Dolphin Directory: ' + folder)
        else:
            print('Directory not found.')

    def _retrieveCurrent(self):
        """retrieve the current version"""
        try:
            link = get_dolphin_link()
            print('Newest Version: ' + os.path.basename(link))
            return link
        except:
            print('Newest version not detected, please contact the developer.')

    def _clearVersion(self):
        """clear out your current version"""
        self.version = ''
        update_user_data(self.path, '')
        print('Version cleared.')

    def _loadData(self):
        """initialize the dolphin path"""
        try:
            self.path, self.version = load_user_data()
        except:
            update_user_data('', '')


def launch_new_instance(args):
    """run the script with args"""
    try:
        script = DolphinCmd(args)
        script.run()

    except KeyboardInterrupt:
        print("Shutdown requested...exiting")


if __name__ == "__main__":
    launch_new_instance(sys.argv[1:])
