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

import imath

import IECore

import Gaffer
import GafferScene
import GafferAppleseed

class AppleseedShaderBall( GafferScene.ShaderBall ) :

	def __init__( self, name = "AppleseedShaderBall" ) :

		GafferScene.ShaderBall.__init__( self, name )

		self["environment"] = Gaffer.FilePathPlug( defaultValue = "${GAFFER_ROOT}/resources/hdri/studio.exr" )

		# Appleseed doesn't support primitives spheres
		self["__sphere"]["type"].setValue( self["__sphere"].Type.Mesh )
		self["__sphere"]["divisions"].setValue( imath.V2i( 60, 120 ) )

		self["__skyDome"] = GafferAppleseed.AppleseedLight()
		self["__skyDome"].loadShader( "latlong_map_environment_edf" )
		self["__skyDome"]["parameters"]["radiance_map"].setInput( self["environment"] )

		self["__skyDome"]["parameters"]["horizontal_shift"].setValue( 90 )

		self["__parentLights"] = GafferScene.Parent()
		self["__parentLights"]["in"].setInput( self._outPlug().getInput() )
		self["__parentLights"]["children"][0].setInput( self["__skyDome"]["out"] )
		self["__parentLights"]["parent"].setValue( "/" )

		self["__appleseedOptions"] = GafferAppleseed.AppleseedOptions()
		self["__appleseedOptions"]["in"].setInput( self["__parentLights"]["out"] )
		self["__appleseedOptions"]["options"]["sampler"]["enabled"].setValue( True )
		self["__appleseedOptions"]["options"]["sampler"]["value"].setValue( 'qmc' )
		self["__appleseedOptions"]["options"]["environmentEDF"]["enabled"].setValue( True )
		self["__appleseedOptions"]["options"]["environmentEDF"]["value"].setValue( '/light' )

		self.addChild(
			self["__appleseedOptions"]["options"]["interactiveRenderMaxSamples"].createCounterpart( "maxSamples", Gaffer.Plug.Direction.In )
		)
		self["__appleseedOptions"]["options"]["interactiveRenderMaxSamples"].setInput( self["maxSamples"] )

		self.addChild(
			self["__appleseedOptions"]["options"]["numThreads"].createCounterpart( "threads", Gaffer.Plug.Direction.In )
		)
		self["__appleseedOptions"]["options"]["numThreads"].setInput( self["threads"] )

		## \todo Consider using an adaptor registry implicitly in the *Render
		# nodes so we don't have to do it explicitly here.
		self["__shaderAdaptor"] = GafferAppleseed.AppleseedShaderAdaptor()
		self["__shaderAdaptor"]["in"].setInput( self["__appleseedOptions"]["out"] )

		self._outPlug().setInput( self["__shaderAdaptor"]["out"] )

IECore.registerRunTimeTyped( AppleseedShaderBall, typeName = "GafferAppleseed::AppleseedShaderBall" )
