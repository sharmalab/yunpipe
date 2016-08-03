'''
This modules is to get credentials for ecs task generation.

It will search ~/.cloud_pipe/task for credentials and configurations for
ecs task. 

It will also allows user to use his/her own credential and configurations by
specify parameter use_user_credential to True
'''

import os
import errno
from configparser import ConfigParser


from . import USER_CREDENTIAL 
from ..utils import get_full_path


def check_task_credential():
    '''
    get the credential and configures stored in ~/.cloud_pipe/task, if there
    is not any, collect those inforamtions and saved in ~/.cloud_pipe
    '''
    folder = get_full_path('~/.cloud_pipe')
    path = get_full_path('~/.cloud_pipe/task')
    config = ConfigParser()
    config.read(path)
    if 'default' not in config:
        aws_access_key_id = input('run task AWS ACCESS KEY ID: ')
        aws_secret_access_key = input('run task AWS SECRET ACCESS KEY: ')
        region = input(
            'Default region name [us-east-1]: ')
        output = input('Default output format [json]: ')

        config.add_section('default')
        config.set('default', 'aws_access_key_id', aws_access_key_id)
        config.set('default', 'aws_secret_access_key', aws_secret_access_key)
        config.set('default', 'region', region)
        config.set('default', 'output', output)

        #
        try:
            os.makedirs(folder)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        with open(path, 'w+') as tmpfile:
            config.write(tmpfile)
    return config


def get_task_credentials(use_user_credential=False):
    '''
    get aws access key id, key, region and output format for ecs task.
    These information will be used for task definition.

    :type: boolean
    :para use_user_credential: whether to use user's more previlledged account

    rtype: dict
    rtype credentials dictionary.
    '''
    if use_user_credential:
        return USER_CREDENTIAL

    config = check_task_credential()
    credentials = {}
    credentials['AWS_DEFAULT_REGION'] = config['default']['region']
    credentials['AWS_DEFAULT_OUTPUT'] = config['default']['output']
    credentials['AWS_ACCESS_KEY_ID'] = config['default']['aws_access_key_id']
    credentials['AWS_SECRET_ACCESS_KEY'] = config['default']['aws_secret_access_key']
    return credentials
