import os
from typing import List, Union, Generator
import datetime
import zlib
from struct import *
from collections import namedtuple
from collections.abc import Container
import xml.etree.ElementTree as ET


class XarInfo(object):
    """Just like TarInfo, a XarInfo represents one member in a XarFile. It does not contain the file data."""

    def __init__(self, name = ''):
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

    def isfile(self) -> bool:
        return self._element.find('type').text == 'file'

    def isdir(self) -> bool:
        return self._element.find('type').text == 'directory'

    
class XarSignature(object):

    @property
    def style(self) -> str:
        return 'RSA'

    @property
    def certificates(self) -> List[x509.Certificate]:
        pass


class XarExtendedSignature(object):
    """Apple only Extended Signature (usually CMS?)"""
    pass



XarHeader = namedtuple('XarHeader', 'magic size version toc_len_compressed toc_len_uncompressed cksumalg')

class XarFile(Container):
    """XAR Archive
    
    This class is written in the style of TarFile
    
    Attributes:
          _toc (xml.etree.ElementTree.Element): The XAR Table of Contents.
          _header (XarHeader): The XAR Header
          _heap_offset (int): The offset into the archive where the heap starts.
          
    See Also:
          - `xar archiver <https://en.wikipedia.org/wiki/Xar_%28archiver%29>`_.
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

    def __init__(self, path: str, toc: ET.Element, header: XarHeader):
        self.path = path
        self._toc = toc
        self._header = header
        self._heap_offset = header.size + header.toc_len_compressed

    @property
    def toc(self):
        return self._toc

    @property
    def signature(self):
        """XAR archives may have a signature, which is commonly used as the package signing method for apple .pkg 
        installers. The signature lives in the XML TOC
        
        See Also:
              - `XML Signature <https://en.wikipedia.org/wiki/XML_Signature>`_.
        """
        signature_info = self._toc.find('signature')
        

    # def _extract_recurse(self, el: ET.Element, destination: str):
    #     for entry in el.findall('file'):
    #         etype = entry.find('type').text
    #         ename = entry.find('name').text
    #
    #         if etype == 'directory':
    #             os.mkdir(os.path.join(destination, ename))
    #             self._extract_recurse(entry, os.path.join(destination, ename))
    #         elif etype == 'file':
    #             fn = os.path.join(destination, ename)
    #             with open(fn, 'w+') as fd:
    #



    # def extract_all(self, destination: str):
    #     if not os.path.exists(destination):
    #         os.mkdir(destination)
    #
    #     self._extract_recurse(self._toc, destination)

    def extract(self, matching: str):
        pass

    def getnames(self) -> List[str]:
        return [m.name for m in self.getmembers()]

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


    @classmethod
    def is_xarfile(cls, name: str) -> bool:
        """Return True if *name* is a xar archive file, that the moxar module can read."""
        with open(name, 'rb') as fd:
            magic = fd.read(4)
            return magic == b'xar!'

    @classmethod
    def open(cls, name: str) -> any:
        with open(name, 'rb') as fd:
            header = fd.read(28)  # The spec says the header must be at least 28

            if header[:4] != b'xar!':
                raise ValueError('Not a XAR Archive')

            hdr = XarHeader._make(XarFile.Header.unpack(header))
            toc_compressed = fd.read(hdr.toc_len_compressed)

        toc_uncompressed = zlib.decompress(toc_compressed)

        if len(toc_uncompressed) != hdr.toc_len_uncompressed:
            raise ValueError('Unexpected TOC Length does not match header')

        toc = ET.fromstring(toc_uncompressed)
        result = XarFile(name, toc, hdr)

        return result
