##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferScene
import GafferRenderMan

## \todo This utterly sucks, because the default RSL shaders
# utterly suck too.
class RenderManShaderBall( GafferScene.ShaderBall ) :

	def __init__( self, name = "RenderManShaderBall" ) :

		GafferScene.ShaderBall.__init__( self, name )

		self["environment"] = Gaffer.StringPlug( defaultValue = "${GAFFER_ROOT}/resources/hdri/studio.exr" )

		self["__envLight"] = GafferRenderMan.RenderManLight()
		self["__envLight"].loadShader( "envlight" )
		self["__envLight"]["parameters"]["envmap"].setInput( self["environment"] )

		self["__parentLights"] = GafferScene.Parent()
		self["__parentLights"]["in"].setInput( self._outPlug().getInput() )
		self["__parentLights"]["child"].setInput( self["__envLight"]["out"] )
		self["__parentLights"]["parent"].setValue( "/" )

		self._outPlug().setInput( self["__parentLights"]["out"] )

IECore.registerRunTimeTyped( RenderManShaderBall, typeName = "GafferRenderMan::RenderManShaderBall" )
