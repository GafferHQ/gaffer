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

import unittest
import imath

import IECore
import IECoreScene

import GafferScene
import GafferSceneTest

class MeshDistortionTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# Input is a plane stretched in X

		plane = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			imath.V2i( 10 )
		)
		plane["Pref"] = plane["P"]
		plane["P"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ p * imath.V3f( 2, 1, 1 ) for p in plane["P"].data ] )
		)

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( plane )

		# Node should do nothing without a filter applied.

		meshDistortion = GafferScene.MeshDistortion()
		meshDistortion["in"].setInput( objectToScene["out"] )

		self.assertScenesEqual( objectToScene["out"], meshDistortion["out"] )
		self.assertSceneHashesEqual( objectToScene["out"], meshDistortion["out"] )

		mesh = meshDistortion["out"].object( "/object" )
		self.assertNotIn( "distortion", mesh )
		self.assertNotIn( "uvDistortion", mesh )

		# Applying a filter should kick it into action.

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )
		meshDistortion["filter"].setInput( f["out"] )

		mesh = meshDistortion["out"].object( "/object" )
		self.assertIn( "distortion", mesh )
		self.assertIn( "uvDistortion", mesh )
		self.assertIsInstance( mesh["distortion"].data, IECore.FloatVectorData )
		self.assertIsInstance( mesh["uvDistortion"].data, IECore.V2fVectorData )

		# We should be able to request only one sort of distortion,
		# or redirect the values to a different primitive variable.

		meshDistortion["distortion"].setValue( "" )
		mesh = meshDistortion["out"].object( "/object" )
		self.assertNotIn( "distortion", mesh )
		self.assertIn( "uvDistortion", mesh )

		meshDistortion["uvDistortion"].setValue( "D" )
		mesh = meshDistortion["out"].object( "/object" )
		self.assertNotIn( "distortion", mesh )
		self.assertNotIn( "uvDistortion", mesh )
		self.assertIn( "D", mesh )

if __name__ == "__main__":
	unittest.main()
