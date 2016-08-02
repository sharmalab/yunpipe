'''

'''
import os
from configparser import ConfigParser

config = ConfigParser()


def find_user_aws_config():
    if 'Windows' in os.environ['OS']:
        AWS_CONFIG_FILE_NAME = os.environ['USERPROFILE'] + '\\.aws\\config'
        AWS_CREDENTIAL_FILE_NAME = \
            os.environ['USERPROFILE'] + '\\.aws\\credentials'
    else:
        AWS_CONFIG_FILE_NAME = os.environ['HOME'] + '/.aws/config'
        AWS_CREDENTIAL_FILE_NAME = os.environ['HOME'] + '/.aws/credentials'

    config.read(AWS_CREDENTIAL_FILE_NAME)
    config.read(AWS_CONFIG_FILE_NAME)


def check_user_aws_config():
    if 'aws_access_key_id' not in config['default'] or\
        'aws_access_key_id' not in config['default']:
    


def find_and_update_config(path, keys):
    '''

    '''
    parser = ConfigParser()
    parser.read(path)
    for key in keys:

