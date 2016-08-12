#!/usr/bin/env python
import json
import argparse

from ..wrapper import describe_algorithm
from ..wrapper import generate_all
from ..utils import get_true_or_false


def main():
    DEFAULT_USER = 'wangyx2005'

    parser = argparse.ArgumentParser(
        description='A tool to wrap your containers')

    parser.add_argument('-d', '--describe', action='store_true',
                        help='use command line editor to describe your algorithm')
    parser.add_argument('-f', '--files', nargs='+',
                        help='List json files to describe your algorithms')
    parser.add_argument('-s', '--show', action='store_true',
                        help='show described algorithm before generate new container')
    parser.add_argument('-r', '--registry', action='store', default='docker hub',
                        help='the registry where you want to upload the container, default is Docker hub')
    parser.add_argument('-u', '--user', action='store', default=DEFAULT_USER,
                        help='user name of docker hub account, default is {}'.format(DEFAULT_USER))

    args = parser.parse_args()

    if args.describe is True and args.files is not None or \
            args.describe is False and args.files is None:
        print('please use either -d or -f flag')
        exit(0)

    if args.describe:
        alg = describe_algorithm()

        if args.show:
            print(json.dumps(alg, indent='    ', sort_keys=True))

        if not get_true_or_false(
                'Do you want to continue generate images? [y/n]:', True):
            exit(0)

        generate_all(alg, args)

    else:
        for file_name in args.files:
            with open(file_name, 'r') as data_file:
                alg = json.load(data_file)
            generate_all(alg, args)


if __name__ == '__main__':
    main()
