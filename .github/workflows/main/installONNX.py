#!/usr/bin/env python3
##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#	 * Redistributions of source code must retain the above copyright
#	   notice, this list of conditions and the following disclaimer.
#
#	 * Redistributions in binary form must reproduce the above copyright
#	   notice, this list of conditions and the following disclaimer in the
#	   documentation and/or other materials provided with the distribution.
#
#	 * Neither the name of Image Engine Design nor the names of any
#	   other contributors to this software may be used to endorse or
#	   promote products derived from this software without specific prior
#	   written permission.
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

import pathlib
import sys
import shutil
import subprocess
from urllib.request import urlretrieve

version = "1.19.2"

if sys.platform == "linux" :
	url = f"https://github.com/microsoft/onnxruntime/releases/download/v{version}/onnxruntime-linux-x64-{version}.tgz"
elif sys.platform == "darwin" :
	url = f"https://github.com/microsoft/onnxruntime/releases/download/v{version}/onnxruntime-osx-arm64-{version}.tgz"
elif sys.platform == "win32" :
	url = f"https://github.com/microsoft/onnxruntime/releases/download/v{version}/onnxruntime-win-x64-{version}.zip"

print( "Downloading ONNX \"{}\"".format( url ) )
archiveFileName, headers = urlretrieve( url )

if sys.platform in ( "linux", "darwin" ) :
	subprocess.check_call(
		[ "tar", "-xf", archiveFileName ]
	)
else :
	subprocess.check_call(
		[ "7z", "x", archiveFileName, "-o./", "-y" ]
	)

shutil.move( pathlib.Path( url ).stem, "onnxruntime" )