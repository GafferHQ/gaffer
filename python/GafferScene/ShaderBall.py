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

## \todo Nice geometry
class ShaderBall( GafferScene.SceneNode ) :

	def __init__( self, name = "ShaderBall" ) :

		GafferScene.SceneNode.__init__( self, name )

		# Public plugs

		self["shader"] = GafferScene.ShaderPlug()
		self["resolution"] = Gaffer.IntPlug( defaultValue = 512, minValue = 0 )

		# Private internal network

		self["__sphere"] = GafferScene.Sphere()
		self["__sphere"]["type"].setValue( GafferScene.Sphere.Type.Primitive )

		self["__camera"] = GafferScene.Camera()
		self["__camera"]["transform"]["translate"]["z"].setValue( 3.5 )

		self["__group"] = GafferScene.Group()
		self["__group"]["in"][0].setInput( self["__sphere"]["out"] )
		self["__group"]["in"][1].setInput( self["__camera"]["out"] )

		self["__subTree"] = GafferScene.SubTree()
		self["__subTree"]["in"].setInput( self["__group"]["out"] )
		self["__subTree"]["root"].setValue( "/group" )

		self["__shaderAssignment"] = GafferScene.ShaderAssignment()
		self["__shaderAssignment"]["in"].setInput( self["__subTree"]["out"] )
		self["__shaderAssignment"]["shader"].setInput( self["shader"] )

		self["__options"] = GafferScene.StandardOptions()
		self["__options"]["in"].setInput( self["__shaderAssignment"]["out"] )

		self["__options"]["options"]["render:camera"]["enabled"].setValue( True )
		self["__options"]["options"]["render:camera"]["value"].setValue( "/camera" )

		self["__options"]["options"]["render:resolution"]["enabled"].setValue( True )
		self["__options"]["options"]["render:resolution"]["value"][0].setInput( self["resolution"] )
		self["__options"]["options"]["render:resolution"]["value"][1].setInput( self["resolution"] )

		self["__emptyScene"] = GafferScene.ScenePlug()
		self["__enabler"] = Gaffer.Switch()
		self["__enabler"].setup( GafferScene.ScenePlug() )
		self["__enabler"]["in"][0].setInput( self["__emptyScene"] )
		self["__enabler"]["in"][1].setInput( self["__options"]["out"] )
		self["__enabler"]["enabled"].setInput( self["enabled"] )
		self["__enabler"]["index"].setValue( 1 )

		self["out"].setFlags( Gaffer.Plug.Flags.Serialisable, False )
		self["out"].setInput( self["__enabler"]["out"] )

	## Internal plug which the final scene is connected into.
	# Derived classes may insert additional nodes between this
	# plug and its input to modify the scene.
	def _outPlug( self ) :

		return self["__enabler"]["in"][1]

IECore.registerRunTimeTyped( ShaderBall, typeName = "GafferScene::ShaderBall" )
