##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import unittest

import IECore
import IECoreScene

import GafferScene
import GafferSceneTest

class PrimitiveQueryTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		cube = GafferScene.Cube()
		mesh = cube["out"].object( "/cube" )

		query = GafferScene.PrimitiveQuery()
		query["scene"].setInput( cube["out"] )
		query["location"].setValue( "/cube" )

		self.assertEqual( query["type"].getValue(), mesh.typeName() )
		self.assertEqual( query["uniform"].getValue(), mesh.variableSize( IECoreScene.PrimitiveVariable.Interpolation.Uniform ) )
		self.assertEqual( query["vertex"].getValue(), mesh.variableSize( IECoreScene.PrimitiveVariable.Interpolation.Vertex ) )
		self.assertEqual( query["varying"].getValue(), mesh.variableSize( IECoreScene.PrimitiveVariable.Interpolation.Varying ) )
		self.assertEqual( query["faceVarying"].getValue(), mesh.variableSize( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying ) )
		self.assertEqual( query["primitive"].getValue(), mesh )

		query["enabled"].setValue( False )
		self.assertEqual( query["type"].getValue(), "" )
		self.assertEqual( query["uniform"].getValue(), 0 )
		self.assertEqual( query["vertex"].getValue(), 0 )
		self.assertEqual( query["varying"].getValue(), 0 )
		self.assertEqual( query["faceVarying"].getValue(), 0 )
		self.assertEqual( query["primitive"].getValue(), IECore.NullObject.defaultNullObject() )

	def testDefaultOutputs( self ) :

		query = GafferScene.PrimitiveQuery()

		def assertDefaults() :
			self.assertEqual( query["type"].getValue(), "" )
			self.assertEqual( query["uniform"].getValue(), 0 )
			self.assertEqual( query["vertex"].getValue(), 0 )
			self.assertEqual( query["varying"].getValue(), 0 )
			self.assertEqual( query["faceVarying"].getValue(), 0 )
			self.assertEqual( query["primitive"].getValue(), IECore.NullObject.defaultNullObject() )

		# No scene connected, no location
		assertDefaults()

		cube = GafferScene.Cube()
		query["scene"].setInput( cube["out"] )

		# Location doesn't exist
		query["location"].setValue( "/missing" )
		assertDefaults()

		# Location exists but holds no primitive (a camera)
		camera = GafferScene.Camera()
		query["scene"].setInput( camera["out"] )
		query["location"].setValue( "/camera" )
		assertDefaults()

if __name__ == "__main__" :
	unittest.main()
