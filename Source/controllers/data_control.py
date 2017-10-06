"""Handle control over user save data"""

import os
import pickle

import subprocess

USER_DATA_PATH = os.path.join(os.getenv('APPDATA'), 'DolphinUpdate/user.data')


def update_user_data(path, version):
    with open(USER_DATA_PATH, 'wb') as file:
        data = {'path': path, 'version': version}
        pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)


def load_user_data():
    with open(USER_DATA_PATH, 'rb') as file:
        data = pickle.load(file)

    return data['path'], data['version']


def extract_7z(zip_file, to_directory):
    """Extract a zip to a directory"""
    proc_args = ['res\\7za', 'x', '-o%s' % to_directory, '-y', '--', zip_file]
    starti = subprocess.STARTUPINFO()
    starti.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.call(proc_args, startupinfo=starti,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE)
