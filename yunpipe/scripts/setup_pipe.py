#!/usr/bin/env python

import argparse
import json

from ..pipeline import set_pipe
from ..pipeline.task_config import get_task_credentials


def main():
    parser = argparse.ArgumentParser(description='A tool to set up your pipeline')

    parser.add_argument('-uu', '--use_user_credential', action='store_true', help='use user credential to run ecs task, we suggest using a less privileged user for running ecs. For more information, see our docs')

    parser.add_argument('-f', '--files', nargs='+',
                        help='json files to describe your work flow')

    args = parser.parse_args()

    if args.files is None:
        print('you need to input at least one file using -f flag')
        exit(0)

    credentials = get_task_credentials(args.use_user_credential)

    for file in args.files:
        with open(file, 'r') as tmpfile:
            user_request = json.load(tmpfile)
        set_pipe.main(user_request, credentials)


if __name__ == '__main__':
    main()
