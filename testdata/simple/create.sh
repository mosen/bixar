#!/usr/bin/env bash

XAR=$(which xar)
$XAR -c -f test.xar ./test.txt

$XAR -c --toc-cksum=sha256 -f test-toc-sha256.xar ./test.txt
$XAR -c --toc-cksum=sha512 -f test-toc-sha512.xar ./test.txt
$XAR -c --file-cksum=sha256 -f test-file-sha256.xar ./test.txt
$XAR -c --file-cksum=sha512 -f test-file-sha512.xar ./test.txt

# Not supported by default on apple distribution
# $XAR -c --compression=lzma -f test-compress-lzma.xar ./test.txt
$XAR -c --compression=bzip2 -f test-compress-bzip2.xar ./test.txt


