'''
Utility functions for cloud_pipe
'''

import os.path


def get_full_path(path):
    '''
    get the absolute path.
    '''
    return os.path.abspath(os.path.expanduser(path))
