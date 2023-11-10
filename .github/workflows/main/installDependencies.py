#!/usr/bin/env python

##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import pathlib
import sys
import argparse
import hashlib
import subprocess
import shutil

if sys.version_info[0] < 3 :
	from urllib import urlretrieve
else :
	from urllib.request import urlretrieve

# Determine default archive URL.

defaultURL = "https://github.com/ImageEngine/cortex/releases/download/10.5.4.0/cortex-10.5.4.0-{platform}-python3.{extension}".format(
	platform = { "darwin" : "osx", "win32" : "windows" }.get( sys.platform, "linux" ),
	extension = "tar.gz" if sys.platform != "win32" else "zip"
)

# Parse command line arguments.

parser = argparse.ArgumentParser()

parser.add_argument(
	"--archiveURL",
	help = "The URL to download the dependencies archive from.",
	default = defaultURL,
)

parser.add_argument(
	"--dependenciesDir",
	help = "The directory to unpack the dependencies into.",
	default = "dependencies",
)

parser.add_argument(
	"--outputFormat",
	help = "A format string that specifies the output printed "
		"by this script. May contain {archiveURL} and {archiveDigest} "
		"tokens that will be substituted appropriately.",
	default = "",
)

args = parser.parse_args()

# Download and unpack the archive.

sys.stderr.write( "Downloading dependencies \"%s\"\n" % args.archiveURL )
archiveFileName, headers = urlretrieve( args.archiveURL )

pathlib.Path( args.dependenciesDir ).mkdir( parents = True )
if sys.platform != "win32" :
	subprocess.check_call( [ "tar", "xf", archiveFileName, "-C", args.dependenciesDir, "--strip-components=1" ] )
else:
	subprocess.check_call(
		[ "7z", "x", archiveFileName, "-o{}".format( args.dependenciesDir ), "-aoa", "-y" ],
		stdout = sys.stderr,
	)
	# 7z (and zip extractors generally) don't have an equivalent of --strip-components=1
	# Copy the files up one directory level to compensate
	extractedPath = pathlib.Path( args.dependenciesDir ) / pathlib.Path( args.archiveURL ).stem
	for p in extractedPath.glob( "*" ) :
		shutil.move( str( p ), args.dependenciesDir )

	extractedPath.rmdir()

# Tell the world

if args.outputFormat :

	md5 = hashlib.md5()
	with open( archiveFileName, mode="rb" ) as f :
		md5.update( f.read() )

	print(
		args.outputFormat.format(
			archiveURL = args.archiveURL,
			archiveDigest = md5.hexdigest()
		)
	)
