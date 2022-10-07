##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import inspect

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class ParentConstraintTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane1 = GafferScene.Plane()
		plane1["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		plane1["transform"]["scale"].setValue( imath.V3f( 1, 2, 3 ) )
		plane1["transform"]["rotate"].setValue( imath.V3f( 1000, 20, 39 ) )
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["name"].setValue( "constrained" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		self.assertSceneValid( group["out"] )

		constraint = GafferScene.ParentConstraint()
		constraint["target"].setValue( "/group/target" )
		constraint["in"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		constraint["filter"].setInput( filter["out"] )

		self.assertSceneValid( constraint["out"] )

		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), group["out"].fullTransform( "/group/target" ) )

		# Test behaviour for missing target
		plane1["name"].setValue( "targetX" )
		with self.assertRaisesRegex( RuntimeError, 'ParentConstraint.__constrainedTransform : Constraint target does not exist: "/group/target"' ):
			constraint["out"].fullTransform( "/group/constrained" )

		constraint["ignoreMissingTarget"].setValue( True )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), constraint["in"].fullTransform( "/group/constrained" ) )

		# Constrain to root and no-op empty constraint ( these are identical for a ParentConstraint )
		constraint["target"].setValue( "/" )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), constraint["in"].fullTransform( "/group/constrained" ) )
		constraint["target"].setValue( "" )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), constraint["in"].fullTransform( "/group/constrained" ) )


	def testRelativeTransform( self ) :

		plane1 = GafferScene.Plane()
		plane1["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		plane1["transform"]["rotate"].setValue( imath.V3f( 0, 90, 0 ) )
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["name"].setValue( "constrained" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		self.assertSceneValid( group["out"] )

		constraint = GafferScene.ParentConstraint()
		constraint["target"].setValue( "/group/target" )
		constraint["in"].setInput( group["out"] )
		constraint["relativeTransform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		constraint["filter"].setInput( filter["out"] )

		self.assertSceneValid( constraint["out"] )

		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) * group["out"].fullTransform( "/group/target" ) )

	def testDirtyPropagation( self ) :

		plane1 = GafferScene.Plane()
		plane2 = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		constraint = GafferScene.ParentConstraint()
		constraint["target"].setValue( "/group/target" )
		constraint["in"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		constraint["filter"].setInput( filter["out"] )

		cs = GafferTest.CapturingSlot( constraint.plugDirtiedSignal() )

		constraint["relativeTransform"]["translate"]["x"].setValue( 10 )

		plugs = { x[0] for x in cs if not x[0].getName().startswith( "__" ) }
		self.assertEqual(
			plugs,
			{
				constraint["relativeTransform"]["translate"]["x"],
				constraint["relativeTransform"]["translate"],
				constraint["relativeTransform"],
				constraint["out"]["bound"],
				constraint["out"]["childBounds"],
				constraint["out"]["transform"],
				constraint["out"]
			}
		)

	def testParentNodeEquivalence( self ) :

		plane1 = GafferScene.Plane()
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["name"].setValue( "constrained" )

		plane1["transform"]["rotate"]["y"].setValue( 45 )
		plane2["transform"]["translate"]["x"].setValue( 1 )

		parent = GafferScene.Parent()
		parent["in"].setInput( plane1["out"] )
		parent["parent"].setValue( "/target" )
		parent["children"][0].setInput( plane2["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		constraint = GafferScene.ParentConstraint()
		constraint["in"].setInput( group["out"] )
		constraint["target"].setValue( "/group/target" )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		constraint["filter"].setInput( filter["out"] )

		self.assertEqual( parent["out"].fullTransform( "/target/constrained" ), constraint["out"].fullTransform( "/group/constrained" ) )

	def testTargetScene( self ) :

		cube = GafferScene.Cube()
		sphere1 = GafferScene.Sphere()
		sphere1["transform"]["translate"]["x"].setValue( 1 )
		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["in"].setInput( cube["out"] )
		parent["child"][0].setInput( sphere1["out"] )

		sphere2 = GafferScene.Sphere()
		sphere2["transform"]["translate"]["y"].setValue( 1 )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint["in"].setInput( parent["out"] )
		constraint["filter"].setInput( cubeFilter["out"] )
		constraint["target"].setValue( "/sphere" )
		self.assertEqual( constraint["out"].fullTransform( "/cube" ), parent["out"].fullTransform( "/sphere" ) )

		constraint["targetScene"].setInput( sphere2["out"] )
		self.assertEqual( constraint["out"].fullTransform( "/cube" ), sphere2["out"].fullTransform( "/sphere" ) )

		sphere2["name"].setValue( "ball" )
		constraint["ignoreMissingTarget"].setValue( True )
		self.assertEqual( constraint["out"].fullTransform( "/cube" ), constraint["in"].fullTransform( "/cube" ) )

	def testTargetVertexSpherePole( self ) :

		target = GafferScene.Sphere()
		target[ "name" ].setValue( "target" )
		target[ "divisions" ].setValue( imath.V2i( 10, 10 ) )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.Vertex )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		# check y axis at pole
		constraint[ "targetVertex" ].setValue( 0 )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )

		# check y axis at pole
		constraint[ "targetVertex" ].setValue( 91 )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 2 ], 1.0, places=6 )

	def testTargetVertexOutOfRange( self ) :

		verticesPerFace = IECore.IntVectorData( [ 4, 4 ] )

		vertexIds = IECore.IntVectorData( [
			0,  3,  4,  1,
			1,  4,  5,  2 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 0.1, 0, 0 ),
			imath.V3f( 0.2, 0, 0 ),
			imath.V3f( 0, 0.1, 0 ),
			imath.V3f( 0.1, 0.1, 0 ),
			imath.V3f( 0.2, 0.1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0, 0 ),
			imath.V2f( 0.5, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0, 1 ),
			imath.V2f( 0.5, 1 ),
			imath.V2f( 1, 1 ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.Vertex )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		for i in range( len( points ) ) :
			constraint[ "targetVertex" ].setValue( i )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertEqual( imath.V3f( m[ 3 ][ 0 ], m[ 3 ][ 1 ], m[ 3 ][ 2 ] ), points[ i ] )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( -1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, -1 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, -1, 0 ) )

		constraint[ "targetVertex" ].setValue( -1 )
		self.assertEqual( constraint[ "targetVertex" ].getValue(), 0 )
		constraint[ "targetVertex" ].setValue( len( points ) + 1 )
		self.assertRaises( Gaffer.ProcessException, lambda : constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ) )

		constraint[ "ignoreMissingTarget" ].setValue( True )

		for i in range( len( points ) ) :
			constraint[ "targetVertex" ].setValue( i )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertEqual( imath.V3f( m[ 3 ][ 0 ], m[ 3 ][ 1 ], m[ 3 ][ 2 ] ), points[ i ] )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( -1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, -1 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, -1, 0 ) )

		constraint[ "targetVertex" ].setValue( -1 )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertEqual( imath.V3f( m[ 3 ][ 0 ], m[ 3 ][ 1 ], m[ 3 ][ 2 ] ), points[ 0 ] )
		self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( -1, 0, 0 ) )
		self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, -1 ) )
		self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, -1, 0 ) )
		constraint[ "targetVertex" ].setValue( len( points ) + 1 )
		self.assertEqual( constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ), imath.M44f() )

	def testTargetVertexCollinearTangent( self ) :

		verticesPerFace = IECore.IntVectorData( [ 3, 3, 3, 3 ] )

		vertexIds = IECore.IntVectorData( [
			1, 0, 2,
			0, 3, 2,
			3, 4, 2,
			4, 1, 2 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0.5, 0, 0.1 ),
			imath.V3f( 0, 0.5, 0.1 ),
			imath.V3f( 0.5, 0.5, 0 ),
			imath.V3f( 1, 0.5, 0.1 ),
			imath.V3f( 0.5, 1, 0.1 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = [
			imath.V2f( 0, 0 ),
			imath.V2f( 0, 0.25 ),
			imath.V2f( 0, 0.5 ),
			imath.V2f( 0, 0.75 ),
			imath.V2f( 0, 1 ),
			imath.V2f( 1, 0.125 ),
			imath.V2f( 0.75, 0.375 ),
			imath.V2f( 0.75, 0.625 ),
			imath.V2f( 1, 0.875 ) ]

		uvs_ct = IECore.V2fVectorData( [ imath.V2f( uv.x, uv.y ) for uv in uvs ], IECore.GeometricData.Interpretation.UV )
		uvs_cb = IECore.V2fVectorData( [ imath.V2f( uv.y, uv.x ) for uv in uvs ], IECore.GeometricData.Interpretation.UV )

		uvIndices = IECore.IntVectorData( [
			0, 1, 5,
			1, 2, 6,
			2, 3, 7,
			3, 4, 8 ] )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.Vertex )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		# colinear tangent
		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, uvs_ct, uvIndices )
		target[ "object" ].setValue( mesh )

		constraint[ "targetVertex" ].setValue( 2 )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertEqual( imath.V3f( m[ 3 ][ 0 ], m[ 3 ][ 1 ], m[ 3 ][ 2 ] ), points[ 2 ] )
		self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, 1 ) )

		# colinear bitangent
		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, uvs_cb, uvIndices )
		target[ "object" ].setValue( mesh )

		constraint[ "targetVertex" ].setValue( 2 )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertEqual( imath.V3f( m[ 3 ][ 0 ], m[ 3 ][ 1 ], m[ 3 ][ 2 ] ), points[ 2 ] )
		self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, 1 ) )

	def testTargetVertexCollapsedTangent( self ) :

		verticesPerFace = IECore.IntVectorData( [ 3, 3, 3, 3 ] )

		vertexIds = IECore.IntVectorData( [
			1, 0, 2,
			0, 3, 2,
			3, 4, 2,
			4, 1, 2 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0.5, 0, 0.1 ),
			imath.V3f( 0, 0.5, 0.1 ),
			imath.V3f( 0.5, 0.5, 0 ),
			imath.V3f( 1, 0.5, 0.1 ),
			imath.V3f( 0.5, 1, 0.1 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = [
			imath.V2f( 0, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0.75, 0 ),
			imath.V2f( 0.75, 0 ),
			imath.V2f( 1, 0 ) ]

		uvs_ct = IECore.V2fVectorData( [ imath.V2f( uv.x, uv.y ) for uv in uvs ], IECore.GeometricData.Interpretation.UV )
		uvs_cb = IECore.V2fVectorData( [ imath.V2f( uv.y, uv.x ) for uv in uvs ], IECore.GeometricData.Interpretation.UV )

		uvIndices = IECore.IntVectorData( [
			0, 0, 1,
			0, 0, 2,
			0, 0, 3,
			0, 0, 4 ] )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.Vertex )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		# collapsed tangent (bitangent not collinear with normal)
		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, uvs_ct, uvIndices )
		target[ "object" ].setValue( mesh )

		constraint[ "targetVertex" ].setValue( 2 )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertEqual( imath.V3f( m[ 3 ][ 0 ], m[ 3 ][ 1 ], m[ 3 ][ 2 ] ), points[ 2 ] )
		self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, 1 ) )

		# collapsed bitangent (tangent not collinear with normal)
		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, uvs_cb, uvIndices )
		target[ "object" ].setValue( mesh )

		constraint[ "targetVertex" ].setValue( 2 )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertEqual( imath.V3f( m[ 3 ][ 0 ], m[ 3 ][ 1 ], m[ 3 ][ 2 ] ), points[ 2 ] )
		self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, 1 ) )

	def testTargetVertexCollapsedNormal( self ) :

		verticesPerFace = IECore.IntVectorData( [ 3, 3 ] )

		vertexIds = IECore.IntVectorData( [
			0, 1, 2,
			1, 0, 2 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 0.5, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0.5, 1 ),
			imath.V2f( 1, 0.5 ),
			imath.V2f( 0, 1 ) ],
			IECore.GeometricData.Interpretation.UV )

		uvIndices = IECore.IntVectorData( [
			0, 1, 3,
			0, 2, 3 ] )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.Vertex )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, uvs, uvIndices )
		target[ "object" ].setValue( mesh )

		constraint[ "targetVertex" ].setValue( 2 )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertEqual( imath.V3f( m[ 3 ][ 0 ], m[ 3 ][ 1 ], m[ 3 ][ 2 ] ), points[ 2 ] )
		self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, 1 ) )

	def testTargetVertexMissingUV( self ) :

		verticesPerFace = IECore.IntVectorData( [ 4, 4 ] )

		vertexIds = IECore.IntVectorData( [
			0,  3,  4,  1,
			1,  4,  5,  2 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 0.1, 0, 0 ),
			imath.V3f( 0.2, 0, 0 ),
			imath.V3f( 0, 0.1, 0 ),
			imath.V3f( 0.1, 0.1, 0 ),
			imath.V3f( 0.2, 0.1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.Vertex )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		for i in range( len( points ) ) :
			constraint[ "targetVertex" ].setValue( i )
			self.assertRaises( Gaffer.ProcessException, lambda : constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ) )

		constraint[ "ignoreMissingTarget" ].setValue( True )

		for i in range( len( points ) ) :
			constraint[ "targetVertex" ].setValue( i )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertEqual( imath.V3f( m[ 3 ][ 0 ], m[ 3 ][ 1 ], m[ 3 ][ 2 ] ), points[ i ] )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( 1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 1, 0 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, 0, 1 ) )

	def testTargetUVOutOfRange( self ) :

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0,  2,  3,  1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 0, 1, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0, 1 ),
			imath.V2f( 1, 1 ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetUV" ].setValue( imath.V2f( -0.5, 0.5 ) )
		self.assertRaises( Gaffer.ProcessException, lambda : constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ) )
		constraint[ "targetUV" ].setValue( imath.V2f( 1.5, 0.5 ) )
		self.assertRaises( Gaffer.ProcessException, lambda : constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ) )
		constraint[ "targetUV" ].setValue( imath.V2f( 0.5, -0.5 ) )
		self.assertRaises( Gaffer.ProcessException, lambda : constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ) )
		constraint[ "targetUV" ].setValue( imath.V2f( 0.5, 1.5 ) )
		self.assertRaises( Gaffer.ProcessException, lambda : constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ) )

		constraint[ "ignoreMissingTarget" ].setValue( True )
		constraint[ "targetUV" ].setValue( imath.V2f( -0.5, 0.5 ) )
		self.assertEqual( constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ), imath.M44f() )
		constraint[ "targetUV" ].setValue( imath.V2f( 1.5, 0.5 ) )
		self.assertEqual( constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ), imath.M44f() )
		constraint[ "targetUV" ].setValue( imath.V2f( 0.5, -0.5 ) )
		self.assertEqual( constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ), imath.M44f() )
		constraint[ "targetUV" ].setValue( imath.V2f( 0.5, 1.5 ) )
		self.assertEqual( constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ), imath.M44f() )

	def testTargetUVEndPoints( self ) :

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0,  2,  3,  1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0.21, 0.14, 0 ),
			imath.V3f( 0.67, 0.14, 0 ),
			imath.V3f( 0.21, 0.76, 0 ),
			imath.V3f( 0.67, 0.76, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0, 1 ),
			imath.V2f( 1, 1 ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		for i in range( len( uvs ) ) :
			constraint[ "targetUV" ].setValue( uvs[ i ] )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertEqual( imath.V3f( m[ 3 ][ 0 ], m[ 3 ][ 1 ], m[ 3 ][ 2 ] ), points[ i ] )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( -1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, -1 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, -1, 0 ) )

	def testTargetUVAxisAlignedEdge( self ) :

		from random import Random
		from datetime import datetime

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0,  2,  3,  1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 0, 1, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0, 1 ),
			imath.V2f( 1, 1 ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		r = Random( datetime.now() )

		# left edge
		for i in range( 10 ) :
			v = r.uniform( uvs[ 0 ][ 1 ], uvs[ 2 ][ 1 ] )
			constraint[ "targetUV" ].setValue( imath.V2f( 0, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( -1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, -1 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, -1, 0 ) )

		# right edge
		for i in range( 10 ) :
			v = r.uniform( uvs[ 1 ][ 1 ], uvs[ 3 ][ 1 ] )
			constraint[ "targetUV" ].setValue( imath.V2f( 1, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], 1.0, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( -1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, -1 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, -1, 0 ) )

		# bottom edge
		for i in range( 10 ) :
			u = r.uniform( uvs[ 0 ][ 0 ], uvs[ 1 ][ 0 ] )
			constraint[ "targetUV" ].setValue( imath.V2f( u, 0 ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( -1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, -1 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, -1, 0 ) )

		# top edge
		for i in range( 10 ) :
			u = r.uniform( uvs[ 2 ][ 0 ], uvs[ 3 ][ 0 ] )
			constraint[ "targetUV" ].setValue( imath.V2f( u, 1 ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], 1.0, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( -1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 0, -1 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, -1, 0 ) )

	def testTargetUVNonLinearUMapping( self ) :

		from random import Random
		from datetime import datetime

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0, 2, 3, 1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0.4, 0, 0 ),
			imath.V3f( 0.6, 0, 0 ),
			imath.V3f( 0, 1, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0, 1 ),
			imath.V2f( 1, 1 ) ],
			IECore.GeometricData.Interpretation.UV )

		uvs_mu = IECore.V2fVectorData( [ imath.V2f( 1.0 - uv.x, uv.y ) for uv in uvs ], IECore.GeometricData.Interpretation.UV )
		uvs_mv = IECore.V2fVectorData( [ imath.V2f( uv.x, 1.0 - uv.y ) for uv in uvs ], IECore.GeometricData.Interpretation.UV )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )
		constraint[ "ignoreMissingTarget" ].setValue( False )

		r = Random( datetime.now() )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )
		target[ "object" ].setValue( mesh )

		for i in range( 10 ) :
			u = 0.5
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

		# mirrored u

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs_mu )
		target[ "object" ].setValue( mesh )

		for i in range( 10 ) :
			u = 0.5
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

		# mirrored v

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs_mv )
		target[ "object" ].setValue( mesh )

		for i in range( 10 ) :
			u = 0.5
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], 1.0 - v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], 1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], 1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVNonLinearVMapping( self ) :

		from random import Random
		from datetime import datetime

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0, 2, 3, 1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0.4, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 0, 0.6, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0, 1 ),
			imath.V2f( 1, 1 ) ],
			IECore.GeometricData.Interpretation.UV )

		uvs_mu = IECore.V2fVectorData( [ imath.V2f( 1.0 - uv.x, uv.y ) for uv in uvs ], IECore.GeometricData.Interpretation.UV )
		uvs_mv = IECore.V2fVectorData( [ imath.V2f( uv.x, 1.0 - uv.y ) for uv in uvs ], IECore.GeometricData.Interpretation.UV )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )
		constraint[ "ignoreMissingTarget" ].setValue( False )

		r = Random( datetime.now() )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )
		target[ "object" ].setValue( mesh )

		for i in range( 10 ) :
			u = r.uniform( 0.0, 1.0 )
			v = 0.5
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

		# mirrored u

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs_mu )
		target[ "object" ].setValue( mesh )

		for i in range( 10 ) :
			u = r.uniform( 0.0, 1.0 )
			v = 0.5
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], 1.0 - u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

		# mirrored v

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs_mv )
		target[ "object" ].setValue( mesh )

		for i in range( 10 ) :
			u = r.uniform( 0.0, 1.0 )
			v = 0.5
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], 1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], 1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVAmbiguousMapping( self ) :

		verticesPerFace = IECore.IntVectorData( [ 4, 4 ] )

		vertexIds = IECore.IntVectorData( [
			0, 3, 4, 1,
			1, 4, 5, 2 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 2, 0, 0 ),
			imath.V3f( 0, 1, 0 ),
			imath.V3f( 1, 1, 0 ),
			imath.V3f( 2, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0.5, 0 ),
			imath.V2f( 0.5, 1 ),
			imath.V2f( 0, 1.5 ),
			imath.V2f( 1, 1.5 ) ],
			IECore.GeometricData.Interpretation.UV )

		uvIndices = IECore.IntVectorData( [
			0, 1, 1, 0,
			2, 2, 3, 3 ] )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, uvs, uvIndices )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		# face 0 (constant u)

		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetUV" ].setValue( imath.V2f( 0.5, 0.5 ) )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 3 ][ 0 ], 0.5, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 1 ], 0.5, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

		constraint[ "ignoreMissingTarget" ].setValue( True )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 3 ][ 0 ], 0.5, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 1 ], 0.5, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

		# face 1 (constant v)

		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetUV" ].setValue( imath.V2f( 0.5, 1.5 ) )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 3 ][ 0 ], 1.5, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 1 ], 0.5, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 0 ], 1.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 1 ], 1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

		constraint[ "ignoreMissingTarget" ].setValue( True )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 3 ][ 0 ], 1.5, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 1 ], 0.5, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 0 ], 1.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 1 ], 1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVCollapsedUTangent( self ) :

		from random import Random
		from datetime import datetime

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0,  2,  3,  1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 1, 1, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0, 1 ),
			imath.V2f( 1, 1 ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		r = Random( datetime.now() )

		for i in range( 10 ) :
			u = r.uniform( 0.0, 1.0 )
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( 1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 1, 0 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, 0, 1 ) )

	def testTargetUVCollapsedVTangent( self ) :

		from random import Random
		from datetime import datetime

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0,  2,  3,  1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 1, 1, 0 ),
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0, 1 ),
			imath.V2f( 1, 1 ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		r = Random( datetime.now() )

		for i in range( 10 ) :
			u = r.uniform( 0.0, 1.0 )
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( 1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 1, 0 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, 0, 1 ) )

	def testTargetUVZeroAreaFace( self ) :

		from random import Random
		from datetime import datetime

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0,  2,  3,  1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0.5, 0.5, 0 ),
			imath.V3f( 0.5, 0.5, 0 ),
			imath.V3f( 0.5, 0.5, 0 ),
			imath.V3f( 0.5, 0.5, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0, 0 ),
			imath.V2f( 1, 0 ),
			imath.V2f( 0, 1 ),
			imath.V2f( 1, 1 ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		r = Random( datetime.now() )

		for i in range( 10 ) :
			u = r.uniform( 0.0, 1.0 )
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], points[ 0 ][ 0 ], places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], points[ 0 ][ 1 ], places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], points[ 0 ][ 2 ], places=6 )
			self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( 1, 0, 0 ) )
			self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 1, 0 ) )
			self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, 0, 1 ) )

	def testTargetUVDegenerateUVVertex( self ) :

		from random import Random
		from datetime import datetime
		r = Random( datetime.now() )

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0, 2, 3, 1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0.0, 0.0, 0 ),
			imath.V3f( 1.0, 0.0, 0 ),
			imath.V3f( 0.0, 1.0, 0 ),
			imath.V3f( 1.0, 1.0, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0.5, 0 ),
			imath.V2f( 0.5, 0 ),
			imath.V2f( 0.0, 1.0 ),
			imath.V2f( 1.0, 1.0 ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		for i in range( 10 ) :
			u = 0.5
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVDegenerateUVVertexLine( self ) :

		from random import Random
		from datetime import datetime
		r = Random( datetime.now() )

		verticesPerFace = IECore.IntVectorData( [ 5 ] )

		vertexIds = IECore.IntVectorData( [
			0, 1, 3, 4, 2 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0.5, 0.0, 0 ),
			imath.V3f( 0.2, 0.6, 0 ),
			imath.V3f( 0.8, 0.6, 0 ),
			imath.V3f( 0.4, 1.0, 0 ),
			imath.V3f( 0.6, 1.0, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0.5, 0 ),
			imath.V2f( 0.5, 0.6 ),
			imath.V2f( 0.5, 0.6 ),
			imath.V2f( 0.5, 1.0 ),
			imath.V2f( 0.5, 1.0 ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		for i in range( 10 ) :
			u = 0.5
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVDegenerateUVVertexLineRotate( self ) :

		from random import Random
		from datetime import datetime
		r = Random( datetime.now() )

		verticesPerFace = IECore.IntVectorData( [ 5 ] )

		vertexIds = IECore.IntVectorData( [
			1, 3, 4, 2, 0 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0.5, 0.0, 0 ),
			imath.V3f( 0.2, 0.6, 0 ),
			imath.V3f( 0.8, 0.6, 0 ),
			imath.V3f( 0.4, 1.0, 0 ),
			imath.V3f( 0.6, 1.0, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( 0.5, 0 ),
			imath.V2f( 0.5, 0.6 ),
			imath.V2f( 0.5, 0.6 ),
			imath.V2f( 0.5, 1.0 ),
			imath.V2f( 0.5, 1.0 ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		for i in range( 10 ) :
			u = 0.5
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVDegenerateFace( self ) :

		from random import Random
		from datetime import datetime

		r = Random( datetime.now() )
		u = r.uniform( 0.0, 1.0 )
		v = r.uniform( 0.0, 1.0 )

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0,  2,  3,  1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0.5, 0.5, 0 ),
			imath.V3f( 0.5, 0.5, 0 ),
			imath.V3f( 0.5, 0.5, 0 ),
			imath.V3f( 0.5, 0.5, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [
			imath.V2f( u, v ),
			imath.V2f( u, v ),
			imath.V2f( u, v ),
			imath.V2f( u, v ) ],
			IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )
		constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 3 ][ 0 ], 0.5, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 1 ], 0.5, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
		self.assertEqual( imath.V3f( m[ 0 ][ 0 ], m[ 0 ][ 1 ], m[ 0 ][ 2 ] ), imath.V3f( 1, 0, 0 ) )
		self.assertEqual( imath.V3f( m[ 1 ][ 0 ], m[ 1 ][ 1 ], m[ 1 ][ 2 ] ), imath.V3f( 0, 1, 0 ) )
		self.assertEqual( imath.V3f( m[ 2 ][ 0 ], m[ 2 ][ 1 ], m[ 2 ][ 2 ] ), imath.V3f( 0, 0, 1 ) )

	def testTargetUVNonConvexPoly( self ) :

		from random import Random
		from datetime import datetime

		verticesPerFace = IECore.IntVectorData( [ 7, 6, 8, 6 ] )

		vertexIds = IECore.IntVectorData( [
			0,  7,  4,  9,  3,  5,  1,
			7, 11, 12,  8, 10,  4,
			4, 10,  8, 12,  6,  5,  3,  9,
			6, 12, 13,  2,  1,  5 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 0.8, 0, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 0.5, 0.1, 0 ),
			imath.V3f( 0.2, 0.2, 0 ),
			imath.V3f( 0.9, 0.2, 0 ),
			imath.V3f( 0.6, 0.3, 0 ),
			imath.V3f( 0, 0.4, 0 ),
			imath.V3f( 0.5, 0.4, 0 ),
			imath.V3f( 0.3, 0.5, 0 ),
			imath.V3f( 0.3, 0.9, 0 ),
			imath.V3f( 0, 1, 0 ),
			imath.V3f( 0.7, 1, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [ imath.V2f( p.x, p.y ) for p in points ], IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		r = Random( datetime.now() )

		for i in range( 10 ) :
			u = r.uniform( 0.0, 1.0 )
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVNonConvexPolyMirroredU( self ) :

		from random import Random
		from datetime import datetime

		verticesPerFace = IECore.IntVectorData( [ 7, 6, 8, 6 ] )

		vertexIds = IECore.IntVectorData( [
			0,  7,  4,  9,  3,  5,  1,
			7, 11, 12,  8, 10,  4,
			4, 10,  8, 12,  6,  5,  3,  9,
			6, 12, 13,  2,  1,  5 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 0.8, 0, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 0.5, 0.1, 0 ),
			imath.V3f( 0.2, 0.2, 0 ),
			imath.V3f( 0.9, 0.2, 0 ),
			imath.V3f( 0.6, 0.3, 0 ),
			imath.V3f( 0, 0.4, 0 ),
			imath.V3f( 0.5, 0.4, 0 ),
			imath.V3f( 0.3, 0.5, 0 ),
			imath.V3f( 0.3, 0.9, 0 ),
			imath.V3f( 0, 1, 0 ),
			imath.V3f( 0.7, 1, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [ imath.V2f( 1.0 - p.x, p.y ) for p in points ], IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		r = Random( datetime.now() )

		for i in range( 10 ) :
			u = r.uniform( 0.0, 1.0 )
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], 1.0 - u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVNonConvexPolyMirroredV( self ) :

		from random import Random
		from datetime import datetime

		verticesPerFace = IECore.IntVectorData( [ 7, 6, 8, 6 ] )

		vertexIds = IECore.IntVectorData( [
			0,  7,  4,  9,  3,  5,  1,
			7, 11, 12,  8, 10,  4,
			4, 10,  8, 12,  6,  5,  3,  9,
			6, 12, 13,  2,  1,  5 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 0.8, 0, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 0.5, 0.1, 0 ),
			imath.V3f( 0.2, 0.2, 0 ),
			imath.V3f( 0.9, 0.2, 0 ),
			imath.V3f( 0.6, 0.3, 0 ),
			imath.V3f( 0, 0.4, 0 ),
			imath.V3f( 0.5, 0.4, 0 ),
			imath.V3f( 0.3, 0.5, 0 ),
			imath.V3f( 0.3, 0.9, 0 ),
			imath.V3f( 0, 1, 0 ),
			imath.V3f( 0.7, 1, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [ imath.V2f( p.x, 1.0 - p.y ) for p in points ], IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		r = Random( datetime.now() )

		for i in range( 10 ) :
			u = r.uniform( 0.0, 1.0 )
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], 1.0 - v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], 1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], 1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVNonConvexPolyMirroredUV( self ) :

		from random import Random
		from datetime import datetime

		verticesPerFace = IECore.IntVectorData( [ 7, 6, 8, 6 ] )

		vertexIds = IECore.IntVectorData( [
			0,  7,  4,  9,  3,  5,  1,
			7, 11, 12,  8, 10,  4,
			4, 10,  8, 12,  6,  5,  3,  9,
			6, 12, 13,  2,  1,  5 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 0.8, 0, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 0.5, 0.1, 0 ),
			imath.V3f( 0.2, 0.2, 0 ),
			imath.V3f( 0.9, 0.2, 0 ),
			imath.V3f( 0.6, 0.3, 0 ),
			imath.V3f( 0, 0.4, 0 ),
			imath.V3f( 0.5, 0.4, 0 ),
			imath.V3f( 0.3, 0.5, 0 ),
			imath.V3f( 0.3, 0.9, 0 ),
			imath.V3f( 0, 1, 0 ),
			imath.V3f( 0.7, 1, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [ imath.V2f( 1.0 - p.x, 1.0 - p.y ) for p in points ], IECore.GeometricData.Interpretation.UV )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		mesh[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		r = Random( datetime.now() )

		for i in range( 10 ) :
			u = r.uniform( 0.0, 1.0 )
			v = r.uniform( 0.0, 1.0 )
			constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
			m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
			self.assertAlmostEqual( m[ 3 ][ 0 ], 1.0 - u, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 1 ], 1.0 - v, places=6 )
			self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 0 ], 1.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 1 ], 1.0, places=6 )
			self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVWindingOrder( self ) :

		verticesPerFace = IECore.IntVectorData( [ 10 ] )

		vertexIds = IECore.IntVectorData( [
			0, 7, 3, 4, 8, 9, 2, 6, 5, 1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 0.6, 0, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 0.2, 0.2, 0 ),
			imath.V3f( 0.4, 0.2, 0 ),
			imath.V3f( 0.6, 0.8, 0 ),
			imath.V3f( 0.8, 0.8, 0 ),
			imath.V3f( 0, 1, 0 ),
			imath.V3f( 0.4, 1, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		uvs = IECore.V2fVectorData( [ imath.V2f( p.x, p.y ) for p in points ], IECore.GeometricData.Interpretation.UV )
		uvs_mu = IECore.V2fVectorData( [ imath.V2f( 1.0 - p.x, p.y ) for p in points ], IECore.GeometricData.Interpretation.UV )
		uvs_mv = IECore.V2fVectorData( [ imath.V2f( p.x, 1.0 - p.y ) for p in points ], IECore.GeometricData.Interpretation.UV )
		uvs_muv = IECore.V2fVectorData( [ imath.V2f( 1.0 - p.x, 1.0 - p.y ) for p in points ], IECore.GeometricData.Interpretation.UV )

		m1 = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		m1[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		m1[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs )

		m2 = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		m2[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		m2[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs_mu )

		m3 = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		m3[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		m3[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs_mv )

		m4 = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		m4[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )
		m4[ "uv" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, uvs_muv )

		t1 = GafferScene.ObjectToScene()
		t1[ "name" ].setValue( "target1" )
		t1[ "object" ].setValue( m1 )

		t2 = GafferScene.ObjectToScene()
		t2[ "name" ].setValue( "target2" )
		t2[ "object" ].setValue( m2 )

		t3 = GafferScene.ObjectToScene()
		t3[ "name" ].setValue( "target3" )
		t3[ "object" ].setValue( m3 )

		t4 = GafferScene.ObjectToScene()
		t4[ "name" ].setValue( "target3" )
		t4[ "object" ].setValue( m4 )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )
		constraint[ "ignoreMissingTarget" ].setValue( False )

		u = 0.47
		v = 0.54

		constraint[ "targetScene" ].setInput( t1[ "out" ] )
		constraint[ "target" ].setValue( "/" + t1[ "name" ].getValue() )
		constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

		constraint[ "targetScene" ].setInput( t2[ "out" ] )
		constraint[ "target" ].setValue( "/" + t2[ "name" ].getValue() )
		constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 3 ][ 0 ], 1.0 - u, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 1 ], v, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 0 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 1 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

		constraint[ "targetScene" ].setInput( t3[ "out" ] )
		constraint[ "target" ].setValue( "/" + t3[ "name" ].getValue() )
		constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 3 ][ 0 ], u, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 1 ], 1.0 - v, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 0 ], 1.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 1 ], 1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

		constraint[ "targetScene" ].setInput( t4[ "out" ] )
		constraint[ "target" ].setValue( "/" + t4[ "name" ].getValue() )
		constraint[ "targetUV" ].setValue( imath.V2f( u, v ) )
		m = constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() )
		self.assertAlmostEqual( m[ 3 ][ 0 ], 1.0 - u, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 1 ], 1.0 - v, places=6 )
		self.assertAlmostEqual( m[ 3 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 0 ], 1.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 0 ][ 2 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 1 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 1 ][ 2 ], -1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 0 ], 0.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 1 ], 1.0, places=6 )
		self.assertAlmostEqual( m[ 2 ][ 2 ], 0.0, places=6 )

	def testTargetUVMissingUV( self ) :

		verticesPerFace = IECore.IntVectorData( [ 4 ] )

		vertexIds = IECore.IntVectorData( [
			0,  2,  3,  1 ] )

		points = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ),
			imath.V3f( 1, 0, 0 ),
			imath.V3f( 0, 1, 0 ),
			imath.V3f( 1, 1, 0 ) ],
			IECore.GeometricData.Interpretation.Point )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds )
		mesh[ "P" ] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, points )

		target = GafferScene.ObjectToScene()
		target[ "name" ].setValue( "target" )
		target[ "object" ].setValue( mesh )

		cube = GafferScene.Cube()
		cube[ "name" ].setValue( "cube" )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter[ "paths" ].setValue( IECore.StringVectorData( [ "/" + cube[ "name" ].getValue() ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint[ "in" ].setInput( cube[ "out" ] )
		constraint[ "filter" ].setInput( cubeFilter[ "out" ] )
		constraint[ "targetScene" ].setInput( target[ "out" ] )
		constraint[ "target" ].setValue( "/" + target[ "name" ].getValue() )
		constraint[ "targetMode" ].setValue( GafferScene.Constraint.TargetMode.UV )
		constraint[ "targetOffset" ].setValue( imath.V3f( 0, 0, 0 ) )

		constraint[ "ignoreMissingTarget" ].setValue( False )
		constraint[ "targetUV" ].setValue( imath.V2f( 0.5, 0.5 ) )
		self.assertRaises( Gaffer.ProcessException, lambda : constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ) )

		constraint[ "ignoreMissingTarget" ].setValue( True )
		constraint[ "targetUV" ].setValue( imath.V2f( 0.5, 0.5 ) )
		self.assertEqual( constraint[ "out" ].fullTransform( "/" + cube[ "name" ].getValue() ), imath.M44f() )

	def testKeepReferencePosition( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			parent["sphere"]["transform"]["translate"]["x"] = context.getFrame()
			"""
		) )

		script["cube"] = GafferScene.Cube()

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["sphere"]["out"] )
		script["parent"]["child"][0].setInput( script["cube"]["out"] )
		script["parent"]["parent"].setValue( "/" )

		script["cubeFilter"] = GafferScene.PathFilter()
		script["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		script["constraint"] = GafferScene.ParentConstraint()
		script["constraint"]["in"].setInput( script["parent"]["out"] )
		script["constraint"]["filter"].setInput( script["cubeFilter"]["out"] )
		script["constraint"]["target"].setValue( "/sphere" )

		script["constraint"]["keepReferencePosition"].setValue( True )

		for frame in range( 0, 10 ) :

			script["constraint"]["referenceFrame"].setValue( frame )

			with Gaffer.Context( script.context() ) as c :

				c.setFrame( frame )

				cubeTransform = script["constraint"]["out"].transform( "/cube" )
				self.assertEqual( cubeTransform, script["constraint"]["in"].transform( "/cube" ) )

				c.setFrame( frame + 1 )
				self.assertEqual(
					script["constraint"]["out"].transform( "/cube" ),
					cubeTransform.translate( imath.V3f( 1, 0, 0 ) )
				)

	def testObjectNonExistentAtReferenceFrame( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["cube"] = GafferScene.Cube()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			parent["sphere"]["transform"]["translate"]["x"] = context.getFrame()
			parent["cube"]["enabled"] = context.getFrame() > 10
			"""
		) )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )
		script["group"]["in"][1].setInput( script["cube"]["out"] )

		script["cubeFilter"] = GafferScene.PathFilter()
		script["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )

		script["constraint"] = GafferScene.ParentConstraint()
		script["constraint"]["in"].setInput( script["group"]["out"] )
		script["constraint"]["filter"].setInput( script["cubeFilter"]["out"] )
		script["constraint"]["target"].setValue( "/group/sphere" )

		script["constraint"]["keepReferencePosition"].setValue( True )
		script["constraint"]["referenceFrame"].setValue( 4 )

		with Gaffer.Context( script.context() ) as context :

			context.setFrame( script["constraint"]["referenceFrame"].getValue() )
			self.assertFalse( script["constraint"]["in"].exists( "/group/cube" ) )

			context.setFrame( 20 )
			self.assertTrue( script["constraint"]["in"].exists( "/group/cube" ) )

			with self.assertRaisesRegex( Gaffer.ProcessException, ".*Constrained object \"/group/cube\" does not exist at reference frame 4" ) :
				script["constraint"]["out"].transform( "/group/cube" )

	def testTargetNonexistentAtReferenceFrame( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["cube"] = GafferScene.Cube()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			parent["sphere"]["transform"]["translate"]["x"] = context.getFrame()
			parent["cube"]["enabled"] = context.getFrame() > 10
			"""
		) )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )
		script["group"]["in"][1].setInput( script["cube"]["out"] )

		script["cubeFilter"] = GafferScene.PathFilter()
		script["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )

		script["constraint"] = GafferScene.ParentConstraint()
		script["constraint"]["in"].setInput( script["group"]["out"] )
		script["constraint"]["filter"].setInput( script["cubeFilter"]["out"] )
		script["constraint"]["target"].setValue( "/group/sphere" )

		script["constraint"]["keepReferencePosition"].setValue( True )
		script["constraint"]["referenceFrame"].setValue( 4 )

		with Gaffer.Context( script.context() ) as context :

			context.setFrame( script["constraint"]["referenceFrame"].getValue() )
			self.assertFalse( script["constraint"]["in"].exists( "/group/cube" ) )

			context.setFrame( 20 )
			self.assertTrue( script["constraint"]["in"].exists( "/group/cube" ) )

			with self.assertRaisesRegex( Gaffer.ProcessException, ".*Constrained object \"/group/cube\" does not exist at reference frame 4" ) :
				script["constraint"]["out"].transform( "/group/cube" )

	def testRelativeTransformIgnoredWhenKeepingReferencePosition( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["cube"] = GafferScene.Cube()

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["sphere"]["out"] )
		script["parent"]["child"][0].setInput( script["cube"]["out"] )
		script["parent"]["parent"].setValue( "/" )

		script["cubeFilter"] = GafferScene.PathFilter()
		script["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		script["constraint"] = GafferScene.ParentConstraint()
		script["constraint"]["in"].setInput( script["parent"]["out"] )
		script["constraint"]["filter"].setInput( script["cubeFilter"]["out"] )
		script["constraint"]["target"].setValue( "/sphere" )

		script["sphereExpression"] = Gaffer.Expression()
		script["sphereExpression"].setExpression( inspect.cleandoc(
			"""
			parent["sphere"]["transform"]["translate"]["x"] = context.getFrame()
			"""
		) )

		# With `keepReferencePosition == False`. The `relativeTransform` is applied.
		# This was essentially a poor man's way of trying to maintain a reference
		# position, where the reference position needed to be manually specified.

		relativeY = 2
		script["constraint"]["relativeTransform"]["translate"]["y"].setValue( relativeY )

		with Gaffer.Context( script.context() ) as context :
			for frame in range( 0, 10 ) :
				context.setFrame( frame )
				self.assertEqual(
					script["constraint"]["out"].transform( "/cube" ),
					imath.M44f().translate( imath.V3f(
						script["sphere"]["transform"]["translate"]["x"].getValue(),
						relativeY,
						0
					) )
				)

		# With `keepReferencePosition == True`. We don't apply the `relativeTransform`.
		# In this mode it is easier to just use the transform tools to interactively
		# adjust the original object's transform until you get what you want. We disable
		# `relativeTransform` in the interests of keeping things simple for the user,
		# and the future possibility of being able to remove it entirely.

		script["constraint"]["keepReferencePosition"].setValue( True )
		script["cube"]["transform"]["translate"]["y"].setValue( 1 )

		with Gaffer.Context( script.context() ) as context :
			for frame in range( 0, 10 ) :
				context.setFrame( frame )
				self.assertEqual(
					script["constraint"]["out"].transform( "/cube" ),
					imath.M44f().translate( imath.V3f(
						script["sphere"]["transform"]["translate"]["x"].getValue() - 1, # Maintaining `x==0`` at frame 1.
						1, # From input transform, _not_ `relativeTransform`.
						0
					) )
				)

		# But of course, that is just what would happen naturally in a naive implementation,
		# because even if the `relativeTransform` was applied, it would be negated by the
		# code that maintains the reference position. Animate the `relativeTransform` so we
		# can be sure it really isn't being applied.

		script["relativeTransformExpression"] = Gaffer.Expression()
		script["relativeTransformExpression"].setExpression( inspect.cleandoc(
			"""
			parent["constraint"]["relativeTransform"]["translate"]["y"] = context.getFrame() * 2
			"""
		) )

		with Gaffer.Context( script.context() ) as context :
			for frame in range( 0, 10 ) :
				context.setFrame( frame )
				self.assertEqual(
					script["constraint"]["out"].transform( "/cube" ),
					imath.M44f().translate( imath.V3f(
						script["sphere"]["transform"]["translate"]["x"].getValue() - 1, # Maintaining `x==0`` at frame 1.
						1, # From input transform, _not_ `relativeTransform`.
						0
					) )
				)

if __name__ == "__main__":
	unittest.main()
