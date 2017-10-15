"""Command line for dolphin update"""

import argparse
import os
import sys
import urllib
import urllib.request
from contextlib import suppress

from controllers.data_control import extract_7z, UserDataControl, rename_7z
from controllers.dolphin_control import get_dolphin_link


class DolphinCmd:
    DOWNLOAD_PATH = os.path.join(os.getenv('APPDATA'), 'DolphinUpdate/')

    def __init__(self, user_data_control, args=None):
        """Perform argument processing and other setup"""
        self._udc = user_data_control
        self.args = args
        self.path = ''
        self.version = ''
        self._init_user_data()

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
        parser.add_argument('-d', '--download', dest='download', action='store_true',
                            help='download the latest version and extract to your directory')
        options = parser.parse_args(self.args)

        # Return the argument values
        return options

    def run(self):
        opt = self.get_cmdline_options()
        if opt.info or not self.args:
            path = self.path
            version = self.version
            print('Dolphin Directory: ' + (path if path else 'Unknown'))
            print('Dolphin Version: ' + (version if version else 'Unknown'))
        if opt.retrieve:
            self._retrieve_current()
        if opt.clear:
            self._clear_version()
        if opt.folder:
            self._set_dolphin_folder(opt.folder)
        if opt.download:
            self._download_new()

    #
    # Private Methods
    #

    def _download_new(self):
        print('Getting newest version...')
        link = self._retrieve_current()
        current = os.path.basename(link)

        if os.path.basename(link) == self.version:
            print('You already have the most recent version.')
            return
        elif not os.path.isdir(self.path):
            print('Your dolphin folder path is invalid.')
            return

        file_name = os.path.basename(link)
        zip_file = os.path.join(self.DOWNLOAD_PATH, file_name)
        to_directory, base_name = os.path.split(self.path)

        try:
            print('Downloading...')
            urllib.request.urlretrieve(link, zip_file)
            print('Downloaded. Extracting...')

            if not os.path.isfile('res/7za.exe'):
                print('Update failed: Please install 7-Zip')
                return

            rename_7z(zip_file, 'Dolphin-x64', base_name)
            extract_7z(zip_file, to_directory)

            print('Update successful.')
            self.version = current
            self._udc.set_user_version(self.version)

        except Exception as error:
            print('Update Failed. %s' % error)

        finally:
            with suppress(FileNotFoundError):
                os.remove(zip_file)

    def _set_dolphin_folder(self, folder):
        if os.path.isdir(folder):
            self.path = folder
            self._udc.set_user_path(folder)

            print('Dolphin Directory: ' + folder)
        else:
            print('Directory not found.')

    def _retrieve_current(self):
        """retrieve the current version"""
        try:
            link = get_dolphin_link()
            print('Newest Version: ' + os.path.basename(link))
            return link

        except:
            print('Newest version not detected, please contact the developer.')

    def _clear_version(self):
        """clear out your current version"""
        self.version = ''
        self._udc.set_user_version(self.version)
        print('Version cleared.')

    def _init_user_data(self):
        """initialize the dolphin path"""
        self.path, self.version = self._udc.load_user_data()


def launch_new_instance(args):
    """run the script with args"""
    try:
        with UserDataControl() as udc:
            script = DolphinCmd(udc, args)
            script.run()

    except KeyboardInterrupt:
        print("Shutdown requested...exiting")


if __name__ == "__main__":
    launch_new_instance(sys.argv[1:])
