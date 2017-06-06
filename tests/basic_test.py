import pytest
import subprocess
import os
from bixar.archive import XarFile
import xml.etree.ElementTree as ET

@pytest.fixture(scope='module',
                params=[
                    '--toc-cksum=sha256',
                    # '--toc-cksum=sha512',
                    # '--file-cksum=sha256',
                    # '--file-cksum=sha512',
                    # '--compression=bzip2'
                ])
def xar(request, tmpdir_factory):
    options = request.param
    fn = tmpdir_factory.mktemp('xartest').join('test.xar')
    fn_source = tmpdir_factory.mktemp('xarsource').join('test.txt')
    fn_source.write('Text to be compressed')

    completed = subprocess.run(["/usr/bin/xar", "-c", "-f", fn, fn_source])
    return fn


@pytest.fixture()
def pkg():
    return os.path.join(os.path.dirname(__file__), '..', 'testdata', 'OneDrive.pkg')

class TestBasic:

    def test_load(self, pkg):
        a = XarFile.open(pkg)
        print(ET.tostring(a.toc))
        names = a.getnames()
        print(names)
        a.extractall('/tmp/od')
