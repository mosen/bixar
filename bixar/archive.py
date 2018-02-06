from __future__ import print_function
from typing import List, Union, Generator, Tuple
import os
import io
import datetime
import zlib
import gzip
import bz2
import hashlib
from struct import *
from collections import namedtuple
import xml.etree.ElementTree as ET

from bixar.errors import XarError, XarChecksumError, XarFormatError


class XarInfo(object):
    """Just like TarInfo, a XarInfo represents one member in a XarFile. It does not contain the file data."""

    def __init__(self, name=''):
        self._name = name

    @classmethod
    def from_element(cls, element: ET.Element):
        x = XarInfo(element.find('name').text)
        x._element = element

        return x

    @property
    def id(self) -> str:
        return self._element.attrib['id']

    @property
    def name(self) -> str:
        return self._element.find('name').text

    @property
    def size(self) -> int:
        return int(self._element.find('size').text)

    @property
    def atime(self) -> Union[datetime.datetime, None]:
        if self._element.find('atime') is not None:
            return datetime.datetime.strptime(self._element.find('atime').text, '%Y-%m-%dT%H:%M:%SZ')
        else:
            return None

    @property
    def mtime(self) -> Union[datetime.datetime, None]:
        if self._element.find('mtime') is not None:
            return datetime.datetime.strptime(self._element.find('mtime').text, '%Y-%m-%dT%H:%M:%SZ')
        else:
            return None

    @property
    def mode(self) -> Union[str, None]:
        if self._element.find('mode') is not None:
            return self._element.find('mode').text
        else:
            return None

    @property
    def uid(self) -> Union[int, None]:
        if self._element.find('uid') is not None:
            return int(self._element.find('uid').text)
        else:
            return None

    @property
    def gid(self) -> Union[int, None]:
        if self._element.find('gid') is not None:
            return int(self._element.find('gid').text)
        else:
            return None

    @property
    def uname(self) -> Union[str, None]:
        user = self._element.find('user')
        if user is not None:
            return user.text
        else:
            return None

    @property
    def gname(self) -> Union[str, None]:
        group = self._element.find('group')
        if group is not None:
            return group.text
        else:
            return None

    @property
    def data(self) -> ET.Element:
        return self._element.find('data')

    @property
    def data_encoding(self) -> str:
        data = self._element.find('data')
        encoding = data.find('encoding').attrib['style']
        return encoding

    @property
    def data_archived_checksum(self) -> Tuple[str, str]:
        """Get the item checksum as Algorithm, Value"""
        data = self._element.find('data')
        cksum = data.find('archived-checksum')
        alg = cksum.attrib['style']
        value = cksum.text

        return alg, value

    def heap_location(self) -> Tuple[int, int]:
        """Get the heap location as length, offset"""
        data = self._element.find('data')
        length = int(data.findtext('length'))
        offset = int(data.findtext('offset'))

        return length, offset

    def isfile(self) -> bool:
        return self._element.find('type').text == 'file'

    def isdir(self) -> bool:
        return self._element.find('type').text == 'directory'

    def xartype(self) -> str:
        return self._element.findtext('type')

#
# class XarSignature(object):
#
#     @property
#     def style(self) -> str:
#         return 'RSA'
#
#     @property
#     def certificates(self) -> List[x509.Certificate]:
#         pass


class XarExtendedSignature(object):
    """Apple only Extended Signature (usually CMS?)"""
    pass


XarHeader = namedtuple('XarHeader', 'magic size version toc_len_compressed toc_len_uncompressed cksumalg')


class XarFile(object):
    """XAR Archive
    
    This class is written in the style of TarFile
    
    Attributes:
          _toc (xml.etree.ElementTree.Element): The XAR Table of Contents.
          _header (XarHeader): The XAR Header
          _heap_offset (int): The offset into the archive where the heap starts.
          
    See Also:
          - `xar archiver <https://en.wikipedia.org/wiki/Xar_%28archiver%29>`_.
          - `mackyle/xar <https://github.com/mackyle/xar/wiki/xarformat>`_.
    """

    def __contains__(self, x):
        """XAR Archive implements __contains__ to allow the expression::
            if 'filename' in archive
        """
        for f in self._toc.iter('file'):
            name = f.find('name').text
            if name == x:
                return True

        return False

    Header = Struct('>4sHHQQI')

    def __init__(self, path=None, mode='rb', fileobj=None):
        if fileobj is None:
            fileobj = open(path, mode)

        header = fileobj.read(28)  # The spec says the header must be at least 28

        if header[:4] != b'xar!':
            raise XarFormatError('Not a XAR Archive')

        hdr = XarHeader._make(XarFile.Header.unpack(header))
        toc_compressed = fileobj.read(hdr.toc_len_compressed)
        toc_uncompressed = zlib.decompress(toc_compressed)

        if len(toc_uncompressed) != hdr.toc_len_uncompressed:
            raise XarFormatError('Unexpected TOC Length does not match header')

        self._toc = ET.fromstring(toc_uncompressed)
        self._fd = fileobj
        self._header = hdr
        self._heap_offset = 28 + hdr.toc_len_compressed

    @property
    def toc(self):
        """Access the TOC document represented by an xml.etree.ElementTree.Element."""
        return self._toc

    @property
    def signature(self):
        """XAR archives may have a signature, which is commonly used as the package signing method for apple .pkg 
        installers. The signature lives in the XML TOC
        
        See Also:
              - `XML Signature <https://en.wikipedia.org/wiki/XML_Signature>`_.
        """
        signature_info = self._toc.find('signature')

    def _extract_xarinfo_bytes(self, xarinfo: XarInfo) -> bytes:
        length, offset = xarinfo.heap_location()
        # print(xarinfo.name)
        # print(self._heap_offset + offset)
        self._fd.seek(self._heap_offset + offset, 0)  # not sure where my offset calc is incorrect
        content = self._fd.read(length)
        # print(ET.tostring(xarinfo.data))
        checksum_algorithm, checksum = xarinfo.data_archived_checksum
        if checksum_algorithm == 'sha1':
            d = hashlib.new('sha1')
            d.update(content)
            hexdigest = d.hexdigest()
            if hexdigest != checksum:
                raise XarChecksumError("Archived Checksum, Expected: {}, Got: {}".format(checksum, hexdigest))

        if xarinfo.data_encoding == 'application/x-gzip':
            return zlib.decompress(content)
        elif xarinfo.data_encoding == 'application/x-bzip2':
            return bz2.decompress(content)
        elif xarinfo.data_encoding == 'application/octet-stream':
            return content.encode('utf8')
        else:
            raise XarFormatError('Unhandled file compression algorithm: {}'.format(xarinfo.data_encoding))

    def _extract_xarinfo(self, xarinfo: XarInfo, destination_filename: str):
        """Extract a file entry using a XarInfo instance."""
        data = self._extract_xarinfo_bytes(xarinfo)
        with open(destination_filename, 'wb') as fd:
            fd.write(data)
            
    def _extract_recursive(self, el: ET.Element, destination: str):
        for entry in el.findall('file'):
            xi = XarInfo.from_element(entry)

            if xi.isdir():
                os.mkdir(os.path.join(destination, xi.name))
                self._extract_recursive(entry, os.path.join(destination, xi.name))
            elif xi.isfile():
                fn = os.path.join(destination, xi.name)
                self._extract_xarinfo(xi, fn)
            else:
                print('Warning: Unhandled XAR Entry Type {}'.format(xi.xartype))


    def _set_attrs_recursive(self, el: ET.Element, destination: str):
        for entry in el.findall('file'):
            xi = XarInfo.from_element(entry)
            abspath = os.path.join(destination, xi.name)

            if xi.isdir():
                if xi.atime is not None and xi.mtime is not None:
                    os.utime(abspath, (xi.atime.timestamp(), xi.mtime.timestamp()))

                if xi.uid is not None and xi.gid is not None:
                    os.chown(abspath, xi.uid, xi.gid)

                self._set_attrs_recursive(entry, abspath)
            elif xi.isfile():
                if xi.atime is not None and xi.mtime is not None:
                    os.utime(abspath, (xi.atime.timestamp(), xi.mtime.timestamp()))

                if xi.uid is not None and xi.gid is not None:
                    os.chown(abspath, xi.uid, xi.gid)

            else:
                raise XarError('Unhandled XAR Entry Type')

    def extractall(self, path='.', members=None, *, numeric_owner=False):
        """Extract all files from the archive to the desired destination."""
        if not os.path.exists(path):
            os.mkdir(path)

        if members is not None:
            raise ValueError('Currently, this parameter is not implemented')
        
        self._extract_recursive(self._toc.find('toc'), path)
        self._set_attrs_recursive(self._toc.find('toc'), path)

    def extract_bytes(self, member: Union[XarInfo, str]) -> Union[None, bytes]:
        """Extract the raw bytes of a single member within the XAR archive."""
        if isinstance(member, str):
            found = self.getmember(member)
            if not found:
                return None
            else:
                member = found

        return self._extract_xarinfo_bytes(member)

    def _getnames(self, element: ET.Element, prefix=''):
        for f in element.findall('file'):
            yield os.path.join(prefix, f.find('name').text)

            if f.findtext('type') == 'directory':
                for cf in self._getnames(f, prefix=prefix + f.findtext('name')):
                    yield cf

    def getnames(self) -> List[str]:
        return [m for m in self._getnames(self._toc.find('toc'))]

    def _getmembers(self, element: ET.Element):
        for f in element.findall('file'):
            yield XarInfo.from_element(f)

            if f.findtext('type') == 'directory':
                for cf in self._getmembers(f):
                    yield cf

    def getmembers(self) -> List[XarInfo]:
        infos = []

        toc = self._toc.find('toc')

        for m in self._getmembers(toc):
            infos.append(m)

        return infos

    def _getmember_recursive(self, el: ET.Element, matching: str, path: str="") -> Union[XarInfo, None]:
        for entry in el.findall('file'):
            xi = XarInfo.from_element(entry)
            abspath = os.path.join(path, xi.name)

            if xi.isdir():
                match = self._getmember_recursive(entry, matching, abspath)
                if match is not None:
                    return match
            elif xi.isfile() and matching == abspath:
                return xi

        return None

    def getmember(self, name: str) -> Union[XarInfo, None]:
        """Get the member matching the absolute path given"""
        toc = self._toc.find('toc')
        return self._getmember_recursive(toc, name)

    @classmethod
    def is_xarfile(cls, name: str) -> bool:
        """Return True if *name* is a xar archive file, that the moxar module can read."""
        with open(name, 'rb') as fd:
            magic = fd.read(4)
            return magic == b'xar!'
