from __future__ import print_function
import argparse
from .archive import XarFile


def main():
    parser = argparse.ArgumentParser(description='bixar test XAR implementation')
    parser.add_argument('-c', help='Creates an archive', action='store_true')
    parser.add_argument('-x', help='Extracts an archive', action='store_true')
    parser.add_argument('-t', help='Lists an archive', action='store_true')
    parser.add_argument('-f',
                        help='Specifies an archive to operate on [REQUIRED!]',
                        required=True, metavar='filename', type=argparse.FileType('rb'))
    parser.add_argument('-v', help='Print filenames as they are archived', action='store_true')

    args = parser.parse_args()

    if args.t:
        return list_archive(args)
    elif args.c:
        print('command not implemented')
        return 1
    elif args.x:
        print('command not implemented')
        return 1

    return 0


def create():
    pass


def extract():
    pass


def list_archive(args):
    archive = XarFile.open(fileobj=args.f)

    for f in archive.getnames():
        print(f)
    
