##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import sys
import ctypes

import IECore

moduleSearchPath = IECore.SearchPath( os.environ["PYTHONPATH"] )
if moduleSearchPath.find( "IECoreUSD" ) and moduleSearchPath.find( "pxr/Usd" ) :

	# Import the USD Python module _without_ RTLD_GLOBAL, otherwise
	# we get errors like the following spewed to the shell when we first
	# open a USD file :
	#
	# ```
	# Coding Error: in DefinePythonClass at line 932 of /disk1/john/dev/gafferDependencies/USD/working/USD-18.09/pxr/base/lib/tf/type.cpp
	# -- TfType 'TfNotice' already has a defined Python type; cannot redefine
	# ```
	#
	# > Note : RTLD_GLOBAL is turned on in the first place by IECore/__init__.py.
	# > Ideally we'd stop doing that and wouldn't need this workaround. See
	# > https://github.com/ImageEngine/cortex/pull/810.

	try :
		if hasattr( sys, "getdlopenflags" ):
			originalDLOpenFlags = sys.getdlopenflags()
			sys.setdlopenflags( originalDLOpenFlags & ~ctypes.RTLD_GLOBAL )
		from pxr import Usd
	finally :
		if hasattr( sys, "getdlopenflags" ):
			sys.setdlopenflags( originalDLOpenFlags )

	# Import IECoreUSD so that we get the USD SceneInterface registered,
	# providing USD functionality to both the SceneReader and SceneWriter.
	import IECoreUSD
