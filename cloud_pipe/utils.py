'''
Utility functions for cloud_pipe
'''

import os.path
import os
import errno


def get_full_path(path):
    '''
    get the absolute path.
    '''
    return os.path.abspath(os.path.expanduser(path))


def create_folder(folder):
    '''
    create folder if not existed
    '''
    try:
        os.makedirs(folder)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
