'''
This module aims to resolve user's aws configurations for boto3.session

The mechanism for this module looks for credentials is to search through a list
of possible locations and stop as soon as it finds credentials. The order in
which this module searches for credentials is:

1. Environment variables
2. Shared credential file (~/.aws/credentials)
3. AWS config file (~/.aws/config)

if credentials or configurations are not found in previous locations, user
will be asked to input corresponding credentials or configurations. Those
informations will be saved in ~/.aws folder

For more information, check boto3 credentials page:
https://boto3.readthedocs.io/en/latest/guide/configuration.html#guide-configuration
'''

import os
import errno
from configparser import ConfigParser

import boto3.session

from ..utils import get_full_path


def find_user_config_path():
    if 'Windows' in os.environ['OS']:
        AWS_FOLDER = os.environ['USERPROFILE'] + '\\.aws'
        AWS_CONFIG_FILE_NAME = os.environ['USERPROFILE'] + '\\.aws\\config'
        AWS_CREDENTIAL_FILE_NAME = \
            os.environ['USERPROFILE'] + '\\.aws\\credentials'
    else:
        AWS_FOLDER = os.environ['USERPROFILE'] + '/.aws'
        AWS_CONFIG_FILE_NAME = os.environ['HOME'] + '/.aws/config'
        AWS_CREDENTIAL_FILE_NAME = os.environ['HOME'] + '/.aws/credentials'

    return AWS_FOLDER, AWS_CONFIG_FILE_NAME, AWS_CREDENTIAL_FILE_NAME


def check_user_aws_credential(AWS_CREDENTIAL_FILE_NAME, AWS_FOLDER):
    '''
    get user credential in ~/.aws/credential folder. if there is not any,
    update that.
    '''
    # check credential file
    config = ConfigParser()
    config.read(AWS_CREDENTIAL_FILE_NAME)
    if 'default' not in config or \
            'aws_access_key_id' not in config['default'] or \
            'aws_secret_access_key' not in config['default']:
        # create the ~/.aws folder
        try:
            os.makedirs(AWS_FOLDER)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        aws_access_key_id = input('AWS ACCESS KEY ID: ')
        aws_secret_access_key = input('AWS SECRET ACCESS KEY: ')
        config.add_section('default')
        config.set('default', 'aws_access_key_id', aws_access_key_id)
        config.set('default', 'aws_secret_access_key', aws_secret_access_key)
        with open(AWS_CREDENTIAL_FILE_NAME, 'a+') as tmpfile:
            config.write(tmpfile)
    else:
        aws_access_key_id = config['default']['aws_access_key_id']
        aws_secret_access_key = config['default']['aws_secret_access_key']
    return aws_access_key_id, aws_secret_access_key


def get_user_aws_config(AWS_CONFIG_FILE_NAME, AWS_FOLDER):
    '''
    get user credential in ~/.aws/config folder. if there is not any, update
    that.
    '''
    config = ConfigParser()
    config.read(AWS_CONFIG_FILE_NAME)
    if 'default' not in config or \
            'region' not in config['default'] or \
            'output' not in config['default']:
        # create the ~/.aws folder
        try:
            os.makedirs(AWS_FOLDER)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        region = input(
            'Default region name [us-east-1]: ')
        output = input('Default output format [json]: ')
        config.add_section('default')
        config.set('default', 'region', region)
        config.set('default', 'output', output)
        with open(AWS_CONFIG_FILE_NAME, 'a+') as tmpfile:
            config.write(tmpfile)
    else:
        region = config['default']['region']
        output = config['default']['output']
    return region, output


def generate_session():
    '''
    generate a boto3.session.Session object using user default aws account

    rtype: boto3.session.Session() object
    '''
    AWS_FOLDER = get_full_path('~/.aws') 
    AWS_CONFIG_FILE_NAME = get_full_path('~/.aws/config')
    AWS_CREDENTIAL_FILE_NAME = get_full_path('~/.aws/credentials')

    # get credentials
    if 'AWS_ACCESS_KEY_ID' not in os.environ or \
            'AWS_SECRET_ACCESS_KEY' not in os.environ:
        aws_access_key_id, aws_secret_access_key = check_user_aws_credential(
            AWS_CREDENTIAL_FILE_NAME, AWS_FOLDER)
    else:
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    # get configs
    if 'AWS_DEFAULT_REGION' not in os.environ or \
            'AWS_DEFAULT_OUTPUT' not in os.environ:
        region, output = get_user_aws_config(AWS_CONFIG_FILE_NAME, AWS_FOLDER)
    else:
        region = os.getenv('AWS_DEFAULT_REGION')
        output = os.getenv('AWS_DEFAULT_OUTPUT')

    # print(aws_access_key_id)
    # print(aws_secret_access_key)
    # print(region)
    # print(output)

    credentials = {}
    credentials['AWS_DEFAULT_REGION'] = region
    credentials['AWS_DEFAULT_OUTPUT'] = output
    credentials['AWS_ACCESS_KEY_ID'] = aws_access_key_id
    credentials['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key

    return credentials, boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region)

if __name__ == '__main__':
    generate_session()
