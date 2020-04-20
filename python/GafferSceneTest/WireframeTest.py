##########################################################################
#
#  Copyright (c) 2018, John Haddon. All rights reserved.
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
import six

import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class WireframeTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 2, 1 ) ) # Two quads

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		wireframe = GafferScene.Wireframe()
		wireframe["in"].setInput( plane["out"] )
		wireframe["filter"].setInput( filter["out"] )
		wireframe["width"].setValue( 2 )

		self.assertSceneValid( wireframe["out"] )

		curves = wireframe["out"].object( "/plane" )
		self.assertIsInstance( curves, IECoreScene.CurvesPrimitive )
		self.assertEqual( curves["width"].data.value, 2 )
		self.assertEqual( curves.bound(), plane["out"].bound( "/plane" ) )

		# Two quads gives 8 edges, but we don't want to repeat the
		# shared edge, hence we expect 7 curves in the output.
		self.assertEqual( len( curves.verticesPerCurve() ), 7 )

	def testUVs( self ) :

		sphere = GafferScene.Sphere()
		sphere["radius"].setValue( 0.1 )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		wireframe = GafferScene.Wireframe()
		wireframe["in"].setInput( sphere["out"] )
		wireframe["filter"].setInput( filter["out"] )
		wireframe["position"].setValue( "uv" )

		self.assertSceneValid( wireframe["out"] )

	def testFaceVaryingUVsWithoutIndices( self ) :

		plane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ), divisions = imath.V2i( 2, 1 ) )
		uv = plane["uv"]
		uv.data = uv.expandedData()
		uv.indices = None
		plane["uv"] = uv

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( plane )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		wireframe = GafferScene.Wireframe()
		wireframe["in"].setInput( objectToScene["out"] )
		wireframe["filter"].setInput( filter["out"] )
		wireframe["position"].setValue( "uv" )

		self.assertSceneValid( wireframe["out"] )

		# Because we removed the indices, there is no connectivity information,
		# and therefore no shared edges, so we expect to see 8 curves.
		curves = wireframe["out"].object( "/object" )
		self.assertEqual( len( curves.verticesPerCurve() ), 8 )

	def testExceptions( self ) :

		plane = GafferScene.Plane()

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		primitiveVariables = GafferScene.PrimitiveVariables()
		primitiveVariables["in"].setInput( plane["out"] )
		primitiveVariables["filter"].setInput( filter["out"] )
		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "constantV3f", IECore.V3fVectorData( [ imath.V3f( 1 ) ] ) ) )
		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "constantString", "test" ) )

		wireframe = GafferScene.Wireframe()
		wireframe["in"].setInput( primitiveVariables["out"] )
		wireframe["filter"].setInput( filter["out"] )

		wireframe["position"].setValue( "notKnownHere" )
		with six.assertRaisesRegex( self, RuntimeError, "MeshPrimitive has no primitive variable named \"notKnownHere\"" ) :
			wireframe["out"].object( "/plane" )

		wireframe["position"].setValue( "constantString" )
		with six.assertRaisesRegex( self, RuntimeError, ".* \"constantString\" has unsupported type \"StringData\"" ) :
			wireframe["out"].object( "/plane" )

		wireframe["position"].setValue( "constantV3f" )
		with six.assertRaisesRegex( self, RuntimeError, ".* \"constantV3f\" must have Vertex, Varying or FaceVarying interpolation" ) :
			wireframe["out"].object( "/plane" )

	def testAdjustBounds( self ) :

		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		wireframe = GafferScene.Wireframe()
		wireframe["in"].setInput( sphere["out"] )
		wireframe["filter"].setInput( sphereFilter["out"] )

		# We don't want to pay for bounds propagation when we're using "P" for the
		# wireframe position. Hash equality indicates a pass-through.

		self.assertScenesEqual( wireframe["in"], wireframe["out"], checks = { "bound" } )
		self.assertSceneHashesEqual( wireframe["in"], wireframe["out"], checks = { "bound" } )

		# But when we use something other than "P", we need the bounds to be updated
		# so as to be valid.

		wireframe["position"].setValue( "uv" )
		self.assertSceneValid( wireframe["out"] )

		# And if we don't want to pay for bounds propagation, we can turn it off,
		# and get back to having a pass-through.

		wireframe["adjustBounds"].setValue( False )
		self.assertScenesEqual( wireframe["in"], wireframe["out"], checks = { "bound" } )
		self.assertSceneHashesEqual( wireframe["in"], wireframe["out"], checks = { "bound" } )

if __name__ == "__main__":
	unittest.main()
