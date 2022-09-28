##########################################################################
#
#  Copyright (c) 2019, Murray Stevenson. All rights reserved.
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
import GafferCycles

class CyclesShaderBall( GafferScene.ShaderBall ) :

	def __init__( self, name = "CyclesShaderBall" ) :

		GafferScene.ShaderBall.__init__( self, name )

		self["environment"] = Gaffer.FilePathPlug( defaultValue = "${GAFFER_ROOT}/resources/hdri/studio.exr" )

		# Cycles doesn't support primitives spheres
		self["__sphere"]["type"].setValue( self["__sphere"].Type.Mesh )
		self["__sphere"]["divisions"].setValue( imath.V2i( 60, 120 ) )

		self["__environmentTexture"] = GafferCycles.CyclesShader()
		self["__environmentTexture"].loadShader( "environment_texture" )
		self["__environmentTexture"]["parameters"]["filename"].setInput( self["environment"] )
		self["__environmentTexture"]["parameters"]["tex_mapping__y_mapping"].setValue( "z" )
		self["__environmentTexture"]["parameters"]["tex_mapping__z_mapping"].setValue( "y" )
		self["__environmentTexture"]["parameters"]["tex_mapping__scale"]["x"].setValue( -1 )

		self["__backgroundLight"] = GafferCycles.CyclesLight()
		self["__backgroundLight"].loadShader( "background_light" )
		self["__backgroundLight"]["parameters"]["color"].setInput( self["__environmentTexture"]["out"]["color"] )
		self["__backgroundLight"]["transform"]["rotate"].setValue( imath.V3f( 0, 90, 0 ) )

		self["__parentLights"] = GafferScene.Parent()
		self["__parentLights"]["in"].setInput( self._outPlug().getInput() )
		self["__parentLights"]["children"][0].setInput( self["__backgroundLight"]["out"] )
		self["__parentLights"]["parent"].setValue( "/" )

		self["__cyclesOptions"] = GafferCycles.CyclesOptions()
		self["__cyclesOptions"]["in"].setInput( self["__parentLights"]["out"] )

		self.addChild(
			self["__cyclesOptions"]["options"]["device"].createCounterpart( "device", Gaffer.Plug.Direction.In )
		)
		Gaffer.MetadataAlgo.copy( self["__cyclesOptions"]["options"]["device"], self["device"], exclude="layout:*" )
		self["__cyclesOptions"]["options"]["device"].setInput( self["device"] )

		self.addChild(
			self["__cyclesOptions"]["options"]["numThreads"].createCounterpart( "threads", Gaffer.Plug.Direction.In )
		)
		self["__cyclesOptions"]["options"]["numThreads"].setInput( self["threads"] )

		self.addChild(
			self["__cyclesOptions"]["options"]["shadingSystem"].createCounterpart( "shadingSystem", Gaffer.Plug.Direction.In )
		)
		Gaffer.MetadataAlgo.copy( self["__cyclesOptions"]["options"]["shadingSystem"], self["shadingSystem"], exclude="layout:*" )
		self["__cyclesOptions"]["options"]["shadingSystem"].setInput( self["shadingSystem"] )

		self._outPlug().setInput( self["__cyclesOptions"]["out"] )

IECore.registerRunTimeTyped( CyclesShaderBall, typeName = "GafferCycles::CyclesShaderBall" )
