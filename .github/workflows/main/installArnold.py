#!/usr/bin/env python
##########################################################################
#
#  Copyright (c) 2021, Hypothetical Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Image Engine Design nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import sys
import argparse
import os
import pathlib
import shutil
import ssl
import subprocess
import urllib.request
import zipfile

platform = { "darwin" : "darwin", "win32" : "windows" }.get( sys.platform, "linux" )
format = { "win32" : "zip" }.get( sys.platform, "tgz" )

parser = argparse.ArgumentParser()

parser.add_argument(
    "--version",
    help = "The Arnold version to install."
)

args = parser.parse_args()

archive = "Arnold-{version}-{platform}.{format}".format(
    version = args.version,
    platform = platform,
    format = format
)

url="https://forgithubci.solidangle.com/arnold/{}".format( archive )

installDir = pathlib.Path.cwd() / "arnoldRoot" / args.version
installDir.mkdir( parents = True, exist_ok = True )
archiveFile = installDir /  archive

print( "Downloading Arnold \"{}\"".format( url ) )

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
httpsHandler = urllib.request.HTTPSHandler( context = context )

passwordManager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
passwordManager.add_password(
    realm = None,
    uri = url,
    user = os.environ["ARNOLD_DOWNLOAD_USER"],
    passwd = os.environ["ARNOLD_DOWNLOAD_PASSWORD"]
)

authHandler = urllib.request.HTTPBasicAuthHandler( passwordManager )
opener = urllib.request.build_opener( httpsHandler, authHandler )

with opener.open( url ) as inFile :
    with open( archiveFile, "wb" ) as outFile :
        shutil.copyfileobj( inFile, outFile )

if format == "tgz" :
    subprocess.check_call( [ "tar", "-xzf", archiveFile, "-C", installDir ] )
elif format == "zip":
    with zipfile.ZipFile( archiveFile ) as f :
        f.extractall( path = installDir )
