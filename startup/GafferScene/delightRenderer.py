##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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
import functools

import IECore
import Gaffer
import GafferScene

# Register function to load renderer on demand. This allows us to find the renderer
# even if the relevant Python module hasn't been imported (in `gaffer execute` for instance).

def __creator( renderType, fileName, messageHandler, renderer ) :

	# Import module to replace ourselves with the true renderer creation function.
	__import__( "IECoreDelight" )
	# And then call `create()` again to use it.
	return GafferScene.Private.IECoreScenePreview.Renderer.create( renderer, renderType, fileName, messageHandler )

for renderer in [ "3Delight", "3Delight Cloud" ] :

	if "DELIGHT" in os.environ and IECore.SearchPath( sys.path ).find( "IECoreDelight" ) :

		if renderer not in GafferScene.Private.IECoreScenePreview.Renderer.types() :
			# Register creator that will load the IECoreDelight module to provide renderer on demand.
			GafferScene.Private.IECoreScenePreview.Renderer.registerType(
				renderer, functools.partial( __creator, renderer = renderer )
			)

		Gaffer.Metadata.registerValue( f"renderer:{renderer}", "ui:enabled", True )

	Gaffer.Metadata.registerValues( {

		f"renderer:{renderer}" : {

			"optionPrefix" : "dl:",
			"attributePrefix" : "dl:",

		},

	} )
