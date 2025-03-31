#!/usr/bin/env python
##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import os
import pathlib
import shutil
import subprocess
import sys

import requests

# RenderMan is only available for download through a web interface connected to
# the RenderMan support forums, and the download requires valid credentials.
# Start by "logging in" with our user name and password. This will return some
# cookies we can use to authenticate our further requests.

cookies = requests.post(
	"https://renderman.pixar.com/forum/member.php",
	{
		"username" : os.environ["RENDERMAN_DOWNLOAD_USER"],
		"password" : os.environ["RENDERMAN_DOWNLOAD_PASSWORD"],
		"url" :  "/forum/",
		"action" : "login"
	}
).cookies

if not { "bbpassword", "bbuserid" }.issubset( cookies.keys() ) :
	sys.stderr.write( "Error : Login failed\n" )
	sys.exit( 1 )

# The various versions of RenderMan are listed on a download page, each
# with a link that takes you to _another_ page which has the file ids
# for the download for each platform. At some point we should scrape that
# to figure out the files given the RenderMan version we want, but for now
# we just hardcode the ids for RenderMan 26.3.

fileId = "12544" if os.name == "nt" else "12545"
fileName = "RenderMan.msi" if os.name == "nt" else "RenderMan.rpm"

# Now we can download our file.

download = requests.get(
	"https://renderman.pixar.com/forum/download.php",
	{
		"fileid" : fileId,
		"distid" : "4483",
		"action" : "dodownload",
	},
	cookies = cookies,
	allow_redirects = True,
	stream = True,
)

with open( fileName, "wb" ) as outFile :
	shutil.copyfileobj( download.raw, outFile )

# Install.

if os.name == "nt" :

	subprocess.check_call(
		[
			"powershell.exe",
			"Start-Process", "msiexec.exe", "-Wait", "-ArgumentList",
			"\"/i {} /qn\"".format( os.path.abspath( fileName ) )
		],
	)

	installLocation = pathlib.Path( "c:\Program Files\Pixar\RenderManProServer-26.3" )

else :

	subprocess.check_call(
		[ "rpm", "-i", fileName ]
	)

	installLocation = pathlib.Path( "/opt/pixar/RenderManProServer-26.3" )

# Remove unnecessary bits. The default installation is a whopping 2.9G, and
# pushes us to the edge of available space on the GitHub runners. We could
# probably be more aggressive if we needed, but this alone clears over 1G.

shutil.rmtree( installLocation / "lib" / "RenderManAssetLibrary" )
shutil.rmtree( installLocation / "lib" / "python2.7" )
shutil.rmtree( installLocation / "lib" / "python3.7" )
shutil.rmtree( installLocation / "lib" / "python3.9" )
shutil.rmtree( installLocation / "lib" / "python3.11" )
shutil.rmtree( installLocation / "lib" / "textures" )

# Install the license file. Details of how we store this securely are
# documented here :
#
#  https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions#storing-large-secrets


subprocess.check_call( [
	"gpg", "--quiet", "--batch", "--yes", "--decrypt",
	f"--passphrase={os.environ['RENDERMAN_LICENSE_PASSPHRASE']}",
	"--output", installLocation.parent / "pixar.license",
	pathlib.Path( __file__ ).parent / "pixar.license.gpg"
] )

print( installLocation )
