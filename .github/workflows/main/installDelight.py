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
import os
import shutil
import subprocess

if sys.version_info[0] < 3 :
    from urllib import urlretrieve
else :
    from urllib.request import urlretrieve

delightVersion="1.1.12"
delightDirectory="free/beta/2018-11-01-oIDoJTpO"

baseUrl = "https://3delight-downloads.s3-us-east-2.amazonaws.com"

if sys.platform.startswith("linux") :  # pre Python 3.3 the major version is added at the end
    package="3DelightNSI-{}-Linux-x86_64".format( delightVersion )

    url = "{baseUrl}/{delightDirectory}/{package}.tar.xz".format(
        baseUrl = baseUrl,
        delightDirectory = delightDirectory,
        package = package
    )

    print( "Downloading 3Delight \"{}\"".format( url ) )
    archiveFileName, headers = urlretrieve( url )

    exitStatus = os.system( "tar -xf {} -C .".format( archiveFileName ) )
    if exitStatus != 0 :
        exit( exitStatus )

    shutil.copytree( "./{}/3delight/Linux-x86_64".format( package ), "./3delight" )

elif sys.platform == "darwin" :
    package="3DelightNSI-{}-Darwin-Universal".format( delightVersion )

    url = "{baseUrl}/{delightDirectory}/{package}.dmg".format(
        baseUrl = baseUrl,
        delightDirectory = delightDirectory,
        package = package
    )

    print( "Downloading 3Delight \"{}\"".format( url ) )
    archiveFileName, headers = urlretrieve( url )

    subprocess.check_call(
        [
            "sudo",
            "hdiutil",
            "mount",
            archiveFileName,
        ]
    )
    subprocess.check_call(
        [
            "sudo",
            "installer",
            "-pkg",
            "/Volumes/3Delight NSI "
            "{delightVersion}/3DelightNSI-{delightVersion}-Darwin-x86_64.pkg".format(
                delightVersion = delightVersion
            ),
            "-target",
            "/",
        ]
    )
    subprocess.check_call(
        [
            "sudo",
            "mv",
            "/Applications/3Delight",
            "./3delight",
        ]
    )


elif sys.platform == "win32":
    package = "3DelightNSI-{}-setup.exe".format( delightVersion )

    url = "{baseUrl}/{delightDirectory}/{package}".format(
        baseUrl = baseUrl,
        delightDirectory = delightDirectory,
        package = package
    )

    print( "Downloading 3Delight \"{}\"".format( url ) )
    archiveFileName, headers = urlretrieve( url )

    subprocess.check_call( [ archiveFileName, "/VERYSILENT", "/DIR=3delight" ] )



