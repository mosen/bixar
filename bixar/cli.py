from __future__ import print_function
import argparse
from .archive import XarFile
from xml.etree import ElementTree
import logging

logger = logging.getLogger(__name__)

  
def main():
    parser = argparse.ArgumentParser(description='bixar test XAR implementation')
    parser.add_argument('-c', help='Creates an archive', action='store_true')
    parser.add_argument('-x', help='Extracts an archive', action='store_true')
    parser.add_argument('-t', help='Lists an archive', action='store_true')
    parser.add_argument('-f',
                        help='Specifies an archive to operate on [REQUIRED!]',
                        required=True, metavar='filename', type=argparse.FileType('rb'))
    parser.add_argument('-C', metavar='path',
                        help='On extract, bixar will chdir to the specified path before extracting the archive.',
                        default='.')
    parser.add_argument('-v', help='Print filenames as they are archived', action='store_true')
    parser.add_argument('--dump-toc', help='Has bixar dump the xml header into the specified file.', metavar='filename')
    parser.add_argument('-k', '--keep-existing', help='Do not overwrite existing files while extracting',
                        action='store_true')

    args = parser.parse_args()

    if args.t:
        return list_archive(args)
    elif args.c:
        print('command not implemented')
        return 1
    elif args.x:
        return extract(args)

    return 0


def create():
    pass


def extract(args):
    logger.error('Extracting from {}'.format(args.f))
    archive = XarFile(fileobj=args.f)

    if args.dump_toc is not None:
        with open(args.dump_toc, 'wb') as fd:
            fd.write(ElementTree.tostring(archive.toc))

    archive.extractall(args.C)


def list_archive(args):
    archive = XarFile(fileobj=args.f)

    if args.dump_toc is not None:
        with open(args.dump_toc, 'wb') as fd:
            fd.write(ElementTree.tostring(archive.toc))

    for f in archive.getnames():
        print(f)

