from __future__ import print_function
import boto3
import json
from time import time

print('Loading lambda function')

client = boto3.client('lambda')

lambda_arn_list = %(lambda_arn_list)s


def lambda_handler(event, context):
    for arn in lambda_arn_list:
        response = client.invoke(
            FunctionName=arn, InvocationType='Event', Payload=event)
