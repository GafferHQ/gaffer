##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

import pathlib
import unittest

import imath
import random

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class MeshSplitTest( GafferSceneTest.SceneTestCase ) :

	# We are assuming that the meshes coming out of MeshSplitter are correct, based on the tests in IECoreScene.
	# We mostly want to check here that the scene structure is coming out right, so we just report each location,
	# and object type or number of mesh faces
	def sceneSummary( self, scenePlug ):
		result = {}

		def walkScene( path ) :
			m = scenePlug.object( path )
			if type( m ) == IECoreScene.MeshPrimitive:
				n = len( m.verticesPerFace )
			else:
				n = type( m )
			result[ GafferScene.ScenePlug.pathToString( path ) ] = n

			childNames = scenePlug.childNames( path )
			for childName in childNames :

				childPath = IECore.InternedStringVectorData( path )
				childPath.append( childName )

				walkScene( childPath )

		walkScene( IECore.InternedStringVectorData() )

		return result

	def test( self ):

		# Set up a scene with a couple of meshes that can be split, plus a couple of things that can't be split
		splitTestMeshReader = GafferScene.SceneReader()
		splitTestMeshReader["fileName"].setValue( pathlib.Path( __file__ ).parent / "usdFiles" / "splitTestMesh.usd" )


		# Even if a MeshSplitter is filtered to a camera, it shouldn't do anything to it
		dontProcess = GafferScene.Camera()
		dontProcess["name"].setValue( 'objectButNotReally' )

		noPrimVars = GafferScene.Sphere()
		noPrimVars["name"].setValue( 'noPrimVars' )

		parent = GafferScene.Parent()
		parent["in"].setInput( splitTestMeshReader["out"] )
		parent["parent"].setValue( '/' )
		parent["children"][0].setInput( noPrimVars["out"] )
		parent["children"][1].setInput( dontProcess["out"] )
		parent["children"][2].setInput( splitTestMeshReader["out"] )

		# Also add some children under one of the splittable meshes to double check name collisions
		# ( BranchCreator should handle this for us, but doesn't hurt to double check we haven't broken anything )
		weirdChild1 = GafferScene.Sphere()
		weirdChild1["name"].setValue( '1' )

		weirdChild2 = GafferScene.Sphere()
		weirdChild2["name"].setValue( 'b' )

		parentWeirdChildren = GafferScene.Parent()
		parentWeirdChildren["in"].setInput( parent["out"] )
		parentWeirdChildren["parent"].setValue( '/object1' )
		parentWeirdChildren["children"][0].setInput( weirdChild1["out"] )
		parentWeirdChildren["children"][1].setInput( weirdChild2["out"] )
		parentWeirdChildren["children"][2].setInput( splitTestMeshReader["out"] )

		filter = GafferScene.PathFilter()

		meshSplit = GafferScene.MeshSplit()
		meshSplit["in"].setInput( parentWeirdChildren["out"] )
		meshSplit["filter"].setInput( filter["out"] )

		self.assertScenesEqual( meshSplit["out"], meshSplit["in"] )
		self.assertSceneValid( meshSplit["out"] )

		filter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )

		with self.assertRaisesRegex( RuntimeError, 'Cannot find primitive variable "segment"' ) :
			meshSplit["out"].childNames( "/object" )

		meshSplit["segment"].setValue( 'uniformString' )

		splitFirstResult = {
			"/" : IECore.NullObject,
			"/object" : IECore.NullObject,
			"/object/0" : 119,
			"/object/1" : 156,
			"/object/2" : 125,
			"/noPrimVars" : 800,
			"/objectButNotReally" : IECoreScene.Camera,
			"/object1" : 400,
			"/object1/1" : 800,
			"/object1/b" : 800,
			"/object1/object" : 400
		}

		self.assertEqual( self.sceneSummary( meshSplit["out"] ), splitFirstResult )
		self.assertSceneValid( meshSplit["out"] )

		filter["paths"].setValue( IECore.StringVectorData( [ '/object', "/object1" ] ) )

		splitBothResult = {
			"/" : IECore.NullObject,
			"/object" : IECore.NullObject,
			"/object/0" : 119,
			"/object/1" : 156,
			"/object/2" : 125,
			"/noPrimVars" : 800,
			"/objectButNotReally" : IECoreScene.Camera,
			"/object1" : IECore.NullObject,
			"/object1/1" : 800,
			"/object1/b" : 800,
			"/object1/object" : 400,
			"/object1/0" : 119,
			"/object1/11" : 156,
			"/object1/2" : 125,
		}

		self.assertEqual( self.sceneSummary( meshSplit["out"] ), splitBothResult )
		self.assertSceneValid( meshSplit["out"] )

		meshSplit["nameFromSegment"].setValue( True )

		splitBothResultWithNames = {
			"/" : IECore.NullObject,
			"/object" : IECore.NullObject,
			"/object/a" : 119,
			"/object/b" : 156,
			"/object/c" : 125,
			"/noPrimVars" : 800,
			"/objectButNotReally" : IECoreScene.Camera,
			"/object1" : IECore.NullObject,
			"/object1/1" : 800,
			"/object1/b" : 800,
			"/object1/object" : 400,
			"/object1/a" : 119,
			"/object1/b1" : 156,
			"/object1/c" : 125,
		}

		self.assertEqual( self.sceneSummary( meshSplit["out"] ), splitBothResultWithNames )
		self.assertSceneValid( meshSplit["out"] )

		# If we include a mesh without the primvar in our filter, we get an error
		meshSplit["nameFromSegment"].setValue( False )
		filter["paths"].setValue( IECore.StringVectorData( [ '/*' ] ) )
		with self.assertRaisesRegex( RuntimeError, 'Cannot find primitive variable "uniformString"' ) :
			meshSplit["out"].childNames( "/noPrimVars" )

		filter["paths"].setValue( IECore.StringVectorData( [ '/object*' ] ) )

		self.assertEqual( self.sceneSummary( meshSplit["out"] ), splitBothResult )
		self.assertSceneValid( meshSplit["out"] )

		filter["paths"].setValue( IECore.StringVectorData( [ '/object1', '/object1/object' ] ) )

		splitNestedResult = {
			"/" : IECore.NullObject,
			"/object" : 400,
			"/noPrimVars" : 800,
			"/objectButNotReally" : IECoreScene.Camera,
			"/object1" : IECore.NullObject,
			"/object1/1" : 800,
			"/object1/b" : 800,
			"/object1/object" : IECore.NullObject,
			"/object1/object/0" : 119,
			"/object1/object/1" : 156,
			"/object1/object/2" : 125,
			"/object1/0" : 119,
			"/object1/11" : 156,
			"/object1/2" : 125,
		}

		self.assertEqual( self.sceneSummary( meshSplit["out"] ), splitNestedResult )
		self.assertSceneValid( meshSplit["out"] )

		# OK, now lets stop mucking about with weird hierarchies and just test a couple of different primvars
		filter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )

		meshSplit["segment"].setValue( 'uniformThickRings' )

		splitRingsResult = {
			"/" : IECore.NullObject,
			"/object" : IECore.NullObject,
			"/object/0" : 40,
			"/object/1" : 40,
			"/object/2" : 40,
			"/object/3" : 40,
			"/object/4" : 40,
			"/object/5" : 40,
			"/object/6" : 40,
			"/object/7" : 40,
			"/object/8" : 40,
			"/object/9" : 40,
			"/noPrimVars" : 800,
			"/objectButNotReally" : IECoreScene.Camera,
			"/object1" : 400,
			"/object1/1" : 800,
			"/object1/b" : 800,
			"/object1/object" : 400
		}


		self.assertEqual( self.sceneSummary( meshSplit["out"] ), splitRingsResult )
		self.assertSceneValid( meshSplit["out"] )

		self.assertEqual(
			[ meshSplit["out"].bound( "/object/%i" % i ) for i in range( 10 ) ],
			[ imath.Box3f( imath.V3f(-1, -1, -1), imath.V3f(1, 1, 1) ) ] * 10
		)

		meshSplit["preciseBounds"].setValue( True )


		self.assertEqual(
			[ meshSplit["out"].bound( "/object/%i" % i ) for i in range( 10 ) ],
			[
				imath.Box3f( imath.V3f(-0.309017062, -0.309017062, 0.95105648), imath.V3f(0.309017062, 0.309017062, 1)),
				imath.Box3f( imath.V3f(-0.587785244, -0.587785244, 0.809017003), imath.V3f(0.587785244, 0.587785244, 0.95105648)),
				imath.Box3f( imath.V3f(-0.809017062, -0.809017062, 0.587785184), imath.V3f(0.809017062, 0.809017062, 0.809017003)),
				imath.Box3f( imath.V3f(-0.95105648, -0.95105648, 0.309017122), imath.V3f(0.95105648, 0.95105648, 0.587785184)),
				imath.Box3f( imath.V3f(-1, -1, 0), imath.V3f(1, 1, 0.309017122)),
				imath.Box3f( imath.V3f(-1, -1, -0.309017062), imath.V3f(1, 1, 0)),
				imath.Box3f( imath.V3f(-0.95105648, -0.95105648, -0.587785184), imath.V3f(0.95105648, 0.95105648, -0.309017062)),
				imath.Box3f( imath.V3f(-0.809017062, -0.809017062, -0.809017003), imath.V3f(0.809017062, 0.809017062, -0.587785184)),
				imath.Box3f( imath.V3f(-0.587785244, -0.587785244, -0.95105654), imath.V3f(0.587785244, 0.587785244, -0.809017003)),
				imath.Box3f( imath.V3f(-0.309016973, -0.309016973, -1), imath.V3f(0.309016973, 0.309016973, -0.95105654))
			]
		)

		self.assertSceneValid( meshSplit["out"] )

		meshSplit["segment"].setValue( 'uniformIndividualFaces' )
		self.assertEqual(
			meshSplit['out'].childNames( "/object" ),
			IECore.InternedStringVectorData( [ str( i ) for i in range( 400 ) ] )
		)
		for i in range( 400 ):
			self.assertEqual(
				len( meshSplit['out'].object( "/object/%i" % i ).verticesPerFace ),
				1
			)
		self.assertSceneValid( meshSplit["out"] )

		meshSplit["nameFromSegment"].setValue( True )
		self.assertEqual( meshSplit["out"].childNames( "/object" ), IECore.InternedStringVectorData( [ "%i"%i for i in range( 0, 800, 2 )] ) )

	def testWithSegment( self ) :

		r = GafferScene.SceneReader()
		r["fileName"].setValue( pathlib.Path( __file__ ).parent / "usdFiles" / "segmentTestMesh.usd" )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		seg = GafferScene.MeshSegments()
		seg["in"].setInput( r["out"] )
		seg["filter"].setInput( f["out"] )
		seg["connectivity"].setValue( "uv" )

		split = GafferScene.MeshSplit()
		split["in"].setInput( seg["out"] )
		split["filter"].setInput( f["out"] )

		faceCountsPerChild = {
			i.value() : len( split["out"].object( "/plane/" + i.value() ).verticesPerFace )
			for i in split["out"].childNames( "/plane" )
		}

		self.assertEqual( faceCountsPerChild, {
			'0': 6, '1': 9, '2': 23, '3': 175, '4': 351, '5': 23, '6': 9, '7': 3,
			'8': 175, '9': 23, '10': 23, '11': 9, '12': 9, '13': 3
		} )

	def testStringFormatAndSort( self ):

		mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( 0 ), imath.V2f( 2 ) ), imath.V2i( 1, 1000 ) )
		mesh["segment"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform,  IECore.V3iVectorData( [imath.V3i( i % 10, ( i // 10 ) % 10, i // 100 ) for i in range( 1000 ) ] ) )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( mesh )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		split = GafferScene.MeshSplit()
		split["in"].setInput( objectToScene["out"] )
		split["filter"].setInput( f["out"] )
		split["nameFromSegment"].setValue( True )

		self.assertEqual(
			split["out"].childNames( "/object" ),
			IECore.InternedStringVectorData( [ "%.f, %.f, %.f" % ( i // 100, ( i // 10 ) % 10, i % 10 ) for i in range( 1000 ) ] )
		)

		def reprMatch( i ):
			if int( i ) == i:
				return repr( int( i ) )
			return repr( i )

		mesh["segment"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform,  IECore.Color3fVectorData( [ imath.Color3f( i * 0.5, i * 0.25, i * 0.125 ) for i in range( 1000 ) ] ) )
		objectToScene["object"].setValue( mesh )
		self.assertEqual(
			split["out"].childNames( "/object" ),
			IECore.InternedStringVectorData( [ reprMatch( i * 0.5 ) + ", " + reprMatch( i * 0.25 ) + ", " + reprMatch( i * 0.125 ) for i in range( 1000 ) ] )
		)

		random.seed( 42 )
		mesh["segment"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform,  IECore.IntVectorData( [ random.randint( 0, 9 ) for i in range( 1000 ) ] ) )
		objectToScene["object"].setValue( mesh )
		self.assertEqual(
			split["out"].childNames( "/object" ),
			IECore.InternedStringVectorData( [ "%i" % i for i in range( 10 ) ] )
		)

		mesh["segment"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform,  IECore.FloatVectorData( [ 1 / ( i + 1 ) for i in range( 1000 ) ] ) )
		objectToScene["object"].setValue( mesh )
		self.assertEqual(
			[ i.value()[:8] for i in split["out"].childNames( "/object" ) ],
			[ repr( 1 / ( 1000 - i ) )[:8] for i in range( 999 ) ] + [ "1" ]
		)

		mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( 0 ), imath.V2f( 2 ) ), imath.V2i( 1, 1 ) )
		mesh["segment"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform,  IECore.M44dVectorData( [ imath.M44d(  1 / 3 ) ] ) )
		objectToScene["object"].setValue( mesh )
		self.assertEqual(
			split["out"].childNames( "/object" ),
			IECore.InternedStringVectorData( [ ", ".join( [ "0.3333333333333333" ] * 16 ) ] )
		)

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod()
	def testStringFormatPerf( self ):

		mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( 0 ), imath.V2f( 2 ) ), imath.V2i( 1000 ) )
		mesh["segment"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform,  IECore.Color3fVectorData( [imath.Color3f( i % 100, ( i / 100 ) % 100, i / 10000 ) for i in range( 1000000 ) ] ) )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( mesh )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )

		split = GafferScene.MeshSplit()
		split["in"].setInput( objectToScene["out"] )
		split["filter"].setInput( f["out"] )
		split["nameFromSegment"].setValue( True )

		with GafferTest.TestRunner.PerformanceScope() :
			split["out"].childNames( "/object" )

if __name__ == "__main__":
	unittest.main()
