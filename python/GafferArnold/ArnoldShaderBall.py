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
import GafferArnold

class ArnoldShaderBall( GafferScene.ShaderBall ) :

	def __init__( self, name = "ArnoldShaderBall" ) :

		GafferScene.ShaderBall.__init__( self, name )

		self["environment"] = Gaffer.FilePathPlug( defaultValue = "${GAFFER_ROOT}/resources/hdri/studio.exr" )

		self["__envMap"] = GafferArnold.ArnoldShader()
		self["__envMap"].loadShader( "image" )
		self["__envMap"]["parameters"]["filename"].setInput( self["environment"] )

		self["__skyDome"] = GafferArnold.ArnoldLight()
		self["__skyDome"].loadShader( "skydome_light" )
		self["__skyDome"]["parameters"]["color"].setInput( self["__envMap"]["out"] )
		self["__skyDome"]["parameters"]["format"].setValue( "latlong" )
		self["__skyDome"]["parameters"]["camera"].setValue( 0 )

		self["__parentLights"] = GafferScene.Parent()
		self["__parentLights"]["in"].setInput( self._outPlug().getInput() )
		self["__parentLights"]["children"][0].setInput( self["__skyDome"]["out"] )
		self["__parentLights"]["parent"].setValue( "/" )

		self["__arnoldOptions"] = GafferArnold.ArnoldOptions()
		self["__arnoldOptions"]["in"].setInput( self["__parentLights"]["out"] )
		self["__arnoldOptions"]["options"]["aaSamples"]["enabled"].setValue( True )
		self["__arnoldOptions"]["options"]["aaSamples"]["value"].setValue( 3 )

		self.addChild(
			self["__arnoldOptions"]["options"]["threads"].createCounterpart( "threads", Gaffer.Plug.Direction.In )
		)
		self["__arnoldOptions"]["options"]["threads"].setInput( self["threads"] )

		self._outPlug().setInput( self["__arnoldOptions"]["out"] )

IECore.registerRunTimeTyped( ArnoldShaderBall, typeName = "GafferArnold::ArnoldShaderBall" )
