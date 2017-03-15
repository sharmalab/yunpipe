import json
from zipfile import ZipFile
import sys
import os

from botocore.exceptions import ClientError
from haikunator import Haikunator

from .image_class import image
from .task_config import get_task_credentials
from . import session
from .. import CLOUD_PIPE_ALGORITHM_FOLDER
from .. import CLOUD_PIPE_TMP_FOLDER
from .. import CLOUD_PIPE_TEMPLATES_FOLDER


WAIT_TIME = 5

name_generator = Haikunator()

LAMBDA_EXEC_TIME = 300

LAMBDA_EXEC_ROLE_NAME = 'lambda_exec_role'

LAMBDA_EXEC_ROLE = {
    "Statement": [
        {
            "Action": [
                "logs:*",
                "cloudwatch:*",
                "lambda:invokeFunction",
                "sqs:SendMessage",
                "ec2:Describe*",
                "ec2:StartInsatnces",
                "iam:PassRole",
                "ecs:RunTask"
            ],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:logs:*:*:*",
                "arn:aws:lambda:*:*:*:*",
                "arn:aws:sqs:*:*:*",
                "arn:aws:ec2:*:*:*",
                "arn:aws:cloudwatch:*:*:*",
                "arn:aws:ecs:*:*:*"
            ]
        }
    ],
    "Version": "2012-10-17"
}


LAMBDA_EXECUTION_ROLE_TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}


# SQS related


def _get_or_create_queue(name):
    '''
    get queue by name, if the queue doesnot exist, create one.

    rtype: string
    '''

    resource = session.resource('sqs')
    if _is_sqs_exist(name):
        return resource.get_queue_by_name(QueueName=name).url
    else:
        return resource.create_queue(QueueName=name).url


def _is_sqs_exist(name):
    '''
    check existense of a given queue
    para: name: sqs name
    type: string
    '''
    queues = session.client('sqs').list_queues()
    if 'QueueUrls' in queues:
        for queue in queues['QueueUrls']:
            if name in queue:
                if name == queue.split('/')[-1]:
                    return True
    return False


def _delete_queue(queue_url):
    session.client('sqs').delete_queue(QueueUrl=queue_url)


def _add_permission_s3_sqs(queue, account_id):
    '''
    add permission to allow s3 put information into sqs
    para: queue
    type: sqs.Queue

    para: account_id: user aws account id
    type: string
    '''
    label = 'S3-SQS' + '-' + name_generator.haikunate()
    queue.add_permission(Label=label, AWSAccountIds=[account_id],
                         Actions=['SendMessage'])

    # change permission to allow everyone, cannot add such permisssion directly
    # ref: https://forums.aws.amazon.com/thread.jspa?threadID=223798
    policy = json.loads(queue.attributes['Policy'])
    new_policy = policy
    new_policy['Statement'][0]['Principal'] = '*'
    queue.set_attributes(Attributes={'Policy': json.dumps(new_policy)})


# S3

S3_EVENT_CONFIGURATIONS = '''
{
    "%(config_name)s": [
        {
            "%(config_arn)s": "%(FunctionArn)s",
            "Events": [
                "s3:ObjectCreated:*"
            ]
        }
    ]
}
'''


def _is_s3_exist(name):
    '''
    check for existense
    '''
    s3 = session.client('s3')
    for bucket in s3.list_buckets()['Buckets']:
        if name == bucket['Name']:
            return True
    return False


def _get_or_create_s3(name):
    '''
    create s3 bucket if not existed
    rtype: string
    '''
    if not _is_s3_exist(name):
        session.client('s3').create_bucket(Bucket=name)
        print('create s3 bucket %s.' % name)
    else:
        print('find s3 bucket %s.' % name)
    return name


def _add_permission_s3_lambda(s3_name, lambda_arn):
    lm = session.client('lambda')
    source = 'arn:aws:s3:::' + s3_name
    func = lm.get_function(FunctionName=lambda_arn)['Configuration']
    lm.add_permission(FunctionName=func['FunctionName'], StatementId='Allow_s3_invoke', Action='lambda:InvokeFunction', Principal='s3.amazonaws.com', SourceArn=source)


def _set_event(name, event_arn, option):
    '''
    set s3 create object to event notification.
    para: name: s3 bucket name
    type: string
    para: event_arn: arn of the event source
    type: string
    para: option: one of these 'lambda', 'sqs', 'sns'
    type: string
    '''
    if option == 'lambda':
        config = S3_EVENT_CONFIGURATIONS % {
            'FunctionArn': event_arn, 'config_name': 'LambdaFunctionConfigurations', 'config_arn': 'LambdaFunctionArn'}
        _add_permission_s3_lambda(name, event_arn)
    elif option == 'sqs':
        config = S3_EVENT_CONFIGURATIONS % {
            'FunctionArn': event_arn, 'config_name': 'QueueConfigurations', 'config_arn': 'QueueArn'}
    elif option == 'sns':
        config = S3_EVENT_CONFIGURATIONS % {
            'FunctionArn': event_arn, 'config_name': 'TopicConfigurations', 'config_arn': 'TopicArn'}
    else:
        print('option needs to be one of the following: labmda, sqs, sns')
        return

    config = json.loads(config)

    session.client('s3').put_bucket_notification_configuration(
        Bucket=name, NotificationConfiguration=config)

    print('finish setup s3 bucket %s event notification' % name)


# ecs
def _generate_task_definition(image_info, user_info, credentials):
    '''
    Based on the algorithm information and the user running information,
    generate task definition
    para image_info: all the required info for running the docker container
    type: image_info class
    para: user_info: passed in information about using the algorithm.
    user_info: {'port' : [], 'variables' = {}}
    type: json

    rtype json
    {
        'taskDefinition': {
            'taskDefinitionArn': 'string',
            'containerDefinitions': [...],
            'family': 'string',
            'revision': 123,
            'volumes': [
                {
                    'name': 'string',
                    'host': {
                        'sourcePath': 'string'
                    }
                },
            ],
            'status': 'ACTIVE'|'INACTIVE',
            'requiresAttributes': [
                {
                    'name': 'string',
                    'value': 'string'
                },
            ]
        }
    }
    '''
    image_info.init_all_variables(user_info, credentials)
    task_def = image_info.generate_task()
    task = session.client('ecs').register_task_definition(family=task_def[
        'family'], containerDefinitions=task_def['containerDefinitions'])
    # task name: task_def['family']
    return task


def _delete_task_definition(task):
    # should be wrong
    # TODO: find the correct way to delete task
    session.client('ecs').deregister_task_definition(taskDefinition=task)

# iam


def create_lambda_exec_role():
    '''
    create lambda_exec_role that allowing lambda function to acess s3,
    sqs, start ec2 and register cloudwatch
    '''
    # create role
    iam = session.client('iam')
    policy = json.dumps(LAMBDA_EXECUTION_ROLE_TRUST_POLICY, sort_keys=True)

    try:
        res = iam.get_role(LAMBDA_EXEC_ROLE_NAME)
        _policy = res['Role']['AssumeRolePolicyDocument']
        if _policy is not None and json.dumps(policy) == policy:
            pass
        else:
            iam.update_assume_role_policy(
                RoleName=LAMBDA_EXEC_ROLE_NAME, PolicyDocument=policy)

    except ClientError:
        print('creating role %s', LAMBDA_EXEC_ROLE_NAME)
        iam.create_role(RoleName=LAMBDA_EXEC_ROLE_NAME,
                        AssumeRolePolicyDocument=policy)
        res = iam.get_role(LAMBDA_EXEC_ROLE_NAME)

    # add policy
    exec_policy = json.dumps(LAMBDA_EXEC_ROLE, sort_keys=True)

    res = iam.list_role_policies(RoleName=LAMBDA_EXEC_ROLE_NAME)

    found = False
    for name in res['PolicyNames']:
        found = (name == 'LambdaExec')
        if found:
            break

    if not found:
        iam.put_role_policy(RoleName=LAMBDA_EXEC_ROLE_NAME, PolicyName='LambdaExec', PolicyDocument=exec_policy)


def _get_role_arn(role_name):
    '''
    '''
    try:
        res = session.client('iam').get_role(RoleName=role_name)
    except ClientError as e:
        print(e)
        print('Does not have role %s, make sure you have permission on creating iam role and run create-lambda-exec-role()', role_name)

    return res['Role']['Arn']


# lambda

def _generate_lambda(image, sys_info, request, task_name):
    '''
    generate lambda function using lambda_run_task_template
    para: image: the informations about using a image
    type: image_class.image_info

    para: sys_info: other system info, see _get_sys_info()
    type: dict

    rtype: string
    '''
    lambda_para = {}
    lambda_para['instance_type'] = image.instance_type
    lambda_para['memory'] = image.memory
    lambda_para['task_name'] = task_name
    lambda_para.update(request)
    lambda_para.update(sys_info)
    file_path = os.path.join(CLOUD_PIPE_TEMPLATES_FOLDER,
            'lambda_run_task_template.txt')
    with open(file_path, 'r') as tmpfile:
        lambda_func = tmpfile.read()
    return lambda_func % lambda_para


# def _add_permission_for_lambda():
#     '''
#     add permission for lambda function allowing acess to s3,
#     sqs, start ec2, register cloudwatch
#     '''
#     # TODO
#     pass


def _create_deploy_package(lambda_code, zipname):
    '''
    generate the deploy package
    '''
    # TODO: check correctness
    file_path = os.path.join(CLOUD_PIPE_TMP_FOLDER, 'lambda_function.py')
    with open(file_path, 'w+') as run_file:
        run_file.write(lambda_code)
    with ZipFile(zipname, 'w') as codezip:
        codezip.write(file_path, arcname='lambda_function.py')
    os.remove(file_path)


def _create_lambda_func(zipname):
    '''
    create lambda function using a .zip deploy package
    '''
    # code = io.BytesIO()
    # with ZipFile(code, 'w') as z:
    #     with ZipFile(zipname, 'r') as datafile:
    #         for file in datafile.namelist():
    #             z.write(file)
    with open(zipname, 'rb') as tmpfile:
        code = tmpfile.read()
    name = name_generator.haikunate()
    role = _get_role_arn(LAMBDA_EXEC_ROLE_NAME)
    res = session.client('lambda').create_function(FunctionName=name, Runtime='python2.7', Role=role, Handler='lambda_function.lambda_handler', Code={'ZipFile': code}, Timeout=LAMBDA_EXEC_TIME, MemorySize=128)

    # TODO: also remove lambda_function.py
    os.remove(zipname)

    return res['FunctionArn']


def _deleta_lambda(name):
    session.client('lambda').delete_function(FunctionName=name)


# utilities for setting up the whole thing

def get_image_info(name):
    '''
    based on the name of the user request, find the image inforomation
    para name: algorithm name
    type: string

    rpara: the infomation of a algorithm, see
    rtype: image_class.image_info
    '''
    # TODO: need to be rewrite down the road
    file_name = name + '_info.json'
    file_path = os.path.join(CLOUD_PIPE_ALGORITHM_FOLDER, file_name)
    with open(file_path, 'r') as tmpfile:
        info = image(json.load(tmpfile))
    return info

def _get_subnet_id():
    from random import randint
    ec2 = session.client('ec2')
    response = ec2.describe_subnets()
    subnet_id = ""
    subnets = response['Subnets']
    if subnets:
        subnet_id = subnets[randint(0,len(subnets)-1)]['SubnetId']
    else:
        pass
        # FIXME:ec2.create_vpc(), ec2.create_subnet()
    return subnet_id
    
def _get_ecs_optimized_AMI_id():
    ec2 = session.client('ec2')
    response = ec2.describe_images(Owners=['amazon',],\
                                   Filters=[{'Name':'name','Values':['amzn-ami-2016.09.f-amazon-ecs-optimized',]},]) 
    ami_id = response['Images'][0]['ImageId']
    return ami_id

def _get_sys_info(key_pair, account_id, region):
    '''
    prepare the system information (non-task specific informations) including
    ec2 image_id, key_pair, security_group, subnet_id, iam_name, region,
    accout_id for making the lambda function.

    rtype dict
    '''
    # TODO: need rewrite this function
    # Look into create_instances(**kwargs) API
    info = {}
    info['image_id'] = _get_ecs_optimized_AMI_id()
    info['iam_name'] = 'ecsInstanceRole' # FIX
    info['subnet_id'] = _get_subnet_id() 
    info['security_group'] = 'default' # FIXME
    info['key_pair'] = key_pair
    info['region'] = region
    info['account_id'] = account_id
    return info


# workflow relation related


def scatter_all(prev_s3, later_lambda_list):
    '''
    used for one-to-all relationship. This utility function create a lambda
    function that invokes the lambda functions in later_lambda_list

    :para: prev_s3: the result s3 bucket of the previous algorithm
    :type: string

    :para: later_lambda_list: a list of sequential algorithms lambda function
        arn list.
    :type: list
    '''
    lambda_list_string = '['
    for arn in later_lambda_list:
        lambda_list_string += arn
        lambda_list_string += ', '
    lambda_list_string = lambda_list_string[:-2] + ']'

    # creating a lambda function that trigger other sequential functions
    file_path = os.path.join(CLOUD_PIPE_TEMPLATES_FOLDER, 'scatter_all.txt')
    with open(file_path, 'r') as tmpfile:
        lambda_code = tmpfile.read() % {'lambda_arn_list': lambda_list_string}

    zipname = os.path.join(CLOUD_PIPE_TMP_FOLDER, '/scatter_all.zip')
    _create_deploy_package(lambda_code, zipname)
    arn = _create_lambda_func(zipname)

    # set previous result s3 bucket to trigger newly created s3 bucket
    _set_event(prev_s3, arn, 'lambda')


def pipeline_setup(request, sys_info, clean, credentials):
    '''
    receive a json format of request, set up one run instance including sqs,
    input/output s3, lambda, (cloudwatch shutdown alarm) and ecs task definition.
    para: request:
    {
        "name": "",
        "port": [],
        "sqs": "",
        "alarm_sqs": "",
        "input_s3_name": "",
        "output_s3_name": "",
        "variables":
        {
            "name": "value"
        }
    }
    type: json

    para:sys_info

    '''
    # set sqs
    request['sqs'] = _get_or_create_queue(request['sqs'])
    clean['sqs'].append(request['sqs'])

    # set ecs task
    image = get_image_info(request['name'])

    # info only need port, variables, output_s3_name, NAME & sqs
    info = {}
    info['port'] = request['port']
    info['variables'] = request['variables']
    # Changable, need to change on senquential run
    info['variables']['output_s3_name'] = request['output_s3_name']
    # QueueUrl
    info['variables']['sqs'] = request['sqs']
    info['variables']['NAME'] = request['name']

    # generate task definition
    task = _generate_task_definition(image, info, credentials)
    clean['task'].append(task['taskDefinition']['taskDefinitionArn'])

    # print(json.dumps(task, sort_keys=True, indent='    '))

    # set lambda
    code = _generate_lambda(image, sys_info, request, task['taskDefinition']['family'])

    zipname = os.path.join(CLOUD_PIPE_TMP_FOLDER, request['name'] + name_generator.haikunate() + '.zip')
    _create_deploy_package(code, zipname)
    lambda_arn = _create_lambda_func(zipname)
    clean['lambda'].append(lambda_arn)

    # set s3
    input_s3 = _get_or_create_s3(request['input_s3_name'])
    _set_event(input_s3, lambda_arn, 'lambda')

    output_s3 = _get_or_create_s3(request['output_s3_name'])
    clean['s3'].append(input_s3)
    clean['s3'].append(output_s3)


def main(user_request, credentials):
    '''
    parse the user_request json, then setup the whole thing
    para: user_request
    type: json

    support only 'single_run' for now
    '''
    sys_info = _get_sys_info(user_request['key_pair'], user_request[
                             'account_id'], user_request['region'])

#    print(json.dumps(sys_info, sort_keys=True, indent='    '))

    clean = {}
    clean['sqs'] = []
    clean['task'] = []
    clean['lambda'] = []
    clean['s3'] = []
    clean['cloudwatch'] = _get_or_create_queue('shutdown_alarm_sqs')

    if user_request['process']['type'] == 'single_run':
        request = {}
        request.update(user_request['process']['algorithms'][0])
        request['input_s3_name'] = user_request['input_s3_name']
        request['output_s3_name'] = user_request['output_s3_name']
        request['sqs'] = name_generator.haikunate()
        request['alarm_sqs'] = clean['cloudwatch']
        pipeline_setup(request, sys_info, clean, credentials)
    elif user_request['process']['type'] == 'sequence_run':
        s3_names = []
        s3_names.append(user_request['input_s3_name'])
        for _ in range(len(user_request['process']['algorithms']) - 1):
            s3_names.append(name_generator.haikunate())
        s3_names.append(user_request['output_s3_name']) 
        i = 0
        for alg in user_request['process']['algorithms']:
            request = {}
            request.update(user_request['process']['algorithms'][i])
            request['input_s3_name'] = s3_names[i]
            request['output_s3_name'] = s3_names[i + 1]
            request['sqs'] = name_generator.haikunate()
            request['alarm_sqs'] = clean['cloudwatch']
            pipeline_setup(request, sys_info, clean, credentials)
            i += 1

    # finish setup
    print('-----------------------------------------------------------')
    print('You can start upload files at %s' % user_request['input_s3_name'])
    print('You will get your result at %s' % user_request['output_s3_name'])
    print('-----------------------------------------------------------')

    file_path = os.path.join(CLOUD_PIPE_TMP_FOLDER, 'clean_up.json')
    with open(file_path, 'w+') as tmpfile:
        json.dump(clean, tmpfile, sort_keys=True, indent='    ')


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as tmpfile:
        user_request = json.load(tmpfile)
    credentials = get_task_credentials()
    main(user_request, credentials)
