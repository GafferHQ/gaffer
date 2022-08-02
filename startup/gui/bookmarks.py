##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
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

import GafferUI

bookmarks = GafferUI.Bookmarks.acquire( application )
bookmarks.setDefault( os.getcwd() )
bookmarks.add( "Home", os.path.expandvars( "$HOME" ) )
bookmarks.add( "Desktop", os.path.expandvars( "$HOME/Desktop" ) )

if os.name == "nt" :
	import string
	from ctypes import windll

	driveMask = windll.kernel32.GetLogicalDrives()
	for letter in string.ascii_uppercase :
		if driveMask & 1 :
			bookmarks.add( "Drives/" + letter + ":", letter + ":/" )

		driveMask >>= 1

fontBookmarks = GafferUI.Bookmarks.acquire( application, category="font" )
fontBookmarks.add( "Gaffer Fonts", os.path.expandvars( "$GAFFER_ROOT/fonts" ) )

shaderBookmarks = GafferUI.Bookmarks.acquire( application, category="shader" )
defaultShaderDirectory = os.path.expandvars( "$HOME/gaffer/shaders" )
try :
	os.makedirs( defaultShaderDirectory )
except OSError :
	# makedirs very unhelpfully raises an exception if
	# the directory already exists, but it might also
	# raise if it fails. we reraise only in the latter case.
	if not os.path.isdir( defaultShaderDirectory ) :
		raise
shaderBookmarks.setDefault( defaultShaderDirectory )
