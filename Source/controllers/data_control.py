"""Handle control over user save data"""

import os
import shelve

import subprocess

USER_DATA_PATH = os.path.join(os.getenv('APPDATA'), 'DolphinUpdate/user.db')


class UserDataControl:
    def __init__(self):
        self._sh = shelve.open(USER_DATA_PATH, writeback=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._sh.close()

    def set_user_path(self, path):
        self._sh['path'] = path

    def set_user_version(self, version):
        self._sh['version'] = version

    def set_auto_launch(self, auto_launch):
        self._sh['auto_launch'] = auto_launch

    def get_auto_launch(self):
        try:
            return self._sh.get('auto_launch', False)
        except:
            self.set_auto_launch(False)
            return False

    def set_hide_changelog(self, hide_status):
        self._sh['hide_changelog'] = hide_status

    def get_hide_changelog(self):
        try:
            return self._sh.get('hide_changelog', False)
        except:
            self.set_hide_changelog(False)
            return False

    def load_user_data(self):
        try:
            return self._sh.get('path', ''), self._sh.get('version', '')
        except:
            self.set_user_path('')
            self.set_user_version('')
            return '', ''


def rename_7z(zip_file, src, dest):
    _call_proc('res\\7za', 'rn', zip_file, src, dest)


def extract_7z(zip_file, to_directory):
    """Extract a zip to a directory"""
    _call_proc('res\\7za', 'x', zip_file, '-o%s' % to_directory, '-y')


def _call_proc(*proc_args):
    starti = subprocess.STARTUPINFO()
    starti.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.call(proc_args, startupinfo=starti,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE)
