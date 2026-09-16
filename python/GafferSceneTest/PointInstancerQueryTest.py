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

import imath

import IECore
import IECoreScene

import GafferScene
import GafferSceneTest

class PointInstancerQueryTest( GafferSceneTest.SceneTestCase ):

	def testBadLocation( self ) :

		for locationExists in ( True, False ) :

			with self.subTest( locationExists = locationExists ) :

				source = GafferScene.Cube()

				query = GafferScene.PointInstancerQuery()
				query["scene"].setInput( source["out"] )
				query["location"].setValue( "/cube" if locationExists else "/missing" )

				self.assertEqual( query["exists"].getValue(), False )
				self.assertEqual( query["prototype"].getValue(), "" )
				self.assertEqual( query["transform"].getValue(), imath.M44f() )
				self.assertEqual( query["visible"].getValue(), False )
				self.assertEqual( query["attributes"].getValue(), IECore.CompoundObject() )

	def testIDExists( self ) :

		# Test without an `instanceId` primitive variable.

		pointsObject = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0 , 2 ) ] ) )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( pointsObject )
		objectToScene["name"].setValue( "instancer" )

		cube = GafferScene.Cube()

		instancerFilter = GafferScene.PathFilter()
		instancerFilter["paths"].setValue( IECore.StringVectorData( [ "/instancer" ] ) )

		pointInstancer = GafferScene.PointInstancer()
		pointInstancer["in"].setInput( objectToScene["out"] )
		pointInstancer["prototypes"].setInput( cube["out"] )
		pointInstancer["filter"].setInput( instancerFilter["out"] )

		query = GafferScene.PointInstancerQuery()
		query["scene"].setInput( pointInstancer["out"] )
		query["location"].setValue( "/instancer" )

		for id, exists in {
			0 : True,
			1 : True,
			2 : False,
			1001 : False,
		}.items() :

			with self.subTest( id = id ) :
				query["id"].setValue( id )
				self.assertEqual( query["exists"].getValue(), exists )

		# Add an `instanceId` primitive variable and retest.

		pointsObject["instanceId"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Int64VectorData( [ 10, 10002 ] )
		)
		objectToScene["object"].setValue( pointsObject )

		for id, exists in {
			0 : False,
			1 : False,
			10 : True,
			11 : False,
			10002 : True,

		}.items() :

			with self.subTest( id = id ) :
				query["id"].setValue( id )
				self.assertEqual( query["exists"].getValue(), exists )

	def testPrototype( self ) :

		plane = GafferScene.Plane()
		cube = GafferScene.Cube()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		pointInstancer = GafferScene.PointInstancer()
		pointInstancer["in"].setInput( plane["out"] )
		pointInstancer["prototypes"].setInput( cube["out"] )
		pointInstancer["filter"].setInput( planeFilter["out"] )
		pointInstancer["prototypesList"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		query = GafferScene.PointInstancerQuery()
		query["scene"].setInput( pointInstancer["out"] )
		query["location"].setValue( "/plane" )

		self.assertEqual( query["prototype"].getValue(), "/plane/prototypes/cube" )

		query["id"].setValue( 4 ) # Out of range
		self.assertEqual( query["prototype"].getValue(), "" )

	def testTransform( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		pointInstancer = GafferScene.PointInstancer()
		pointInstancer["in"].setInput( plane["out"] )
		pointInstancer["filter"].setInput( planeFilter["out"] )

		query = GafferScene.PointInstancerQuery()
		query["scene"].setInput( pointInstancer["out"] )
		query["location"].setValue( "/plane" )

		for i in range( 4 ) :
			with self.subTest( id = i ) :
				query["id"].setValue( i )
				self.assertEqual(
					query["transform"].getValue(),
					imath.M44f().translate(
						plane["out"].object( "/plane" )["P"].data[i]
					)
				)

		query["id"].setValue( 4 ) # Out of range
		self.assertEqual( query["transform"].getValue(), imath.M44f() )

	def testVisibility( self ) :

		pointsObject = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 2 ) )
		pointsObject["invisibleIds"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.Int64VectorData( [ 0 ] )
		)
		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( pointsObject )
		objectToScene["name"].setValue( "instancer" )

		instancerFilter = GafferScene.PathFilter()
		instancerFilter["paths"].setValue( IECore.StringVectorData( [ "/instancer" ] ) )

		pointInstancer = GafferScene.PointInstancer()
		pointInstancer["in"].setInput( objectToScene["out"] )
		pointInstancer["filter"].setInput( instancerFilter["out"] )

		query = GafferScene.PointInstancerQuery()
		query["scene"].setInput( pointInstancer["out"] )
		query["location"].setValue( "/instancer" )

		for id, visible in {
			0 : False,
			1 : True,
			2 : False,
		}.items() :

			with self.subTest( id = id ) :
				query["id"].setValue( id )
				self.assertEqual( query["visible"].getValue(), visible )

	def testAttributes( self ) :

		pointsObject = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 2 ) )
		pointsObject["int"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1 ] )
		)
		pointsObject["float"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 0, 1 ] )
		)
		pointsObject["vector"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData( [ imath.V3f( 0 ), imath.V3f( 1 ) ] )
		)
		pointsObject["color"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Color3fVectorData( [ imath.Color3f( 0 ), imath.Color3f( 1 ) ] )
		)
		pointsObject["string"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.StringVectorData( [ "0", "1" ] )
		)
		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( pointsObject )
		objectToScene["name"].setValue( "instancer" )

		instancerFilter = GafferScene.PathFilter()
		instancerFilter["paths"].setValue( IECore.StringVectorData( [ "/instancer" ] ) )

		pointInstancer = GafferScene.PointInstancer()
		pointInstancer["in"].setInput( objectToScene["out"] )
		pointInstancer["filter"].setInput( instancerFilter["out"] )

		query = GafferScene.PointInstancerQuery()
		query["scene"].setInput( pointInstancer["out"] )
		query["location"].setValue( "/instancer" )

		for id in range( 2 ) :

			with self.subTest( id = id ) :

				query["id"].setValue( id )
				self.assertEqual(
					query["attributes"].getValue(),
					IECore.CompoundObject( {
						"int" : IECore.IntData( id ),
						"float" : IECore.FloatData( id ),
						"vector" : IECore.V3fData( imath.V3f( id ) ),
						"color" : IECore.Color3fData( imath.Color3f( id ) ),
						"string" : IECore.StringData( str( id ) ),
					} )
				)

	def testIndexedAttribute( self ) :

		pointsObject = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 1000 ) )
		pointsObject["attribute"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Color3fVectorData( [ imath.Color3f( 0.5 ), imath.Color3f( 1.0 ) ] ),
			IECore.IntVectorData( [ 0, 1 ] * 500 )
		)
		self.assertTrue( pointsObject.arePrimitiveVariablesValid() )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( pointsObject )
		objectToScene["name"].setValue( "instancer" )

		instancerFilter = GafferScene.PathFilter()
		instancerFilter["paths"].setValue( IECore.StringVectorData( [ "/instancer" ] ) )

		pointInstancer = GafferScene.PointInstancer()
		pointInstancer["in"].setInput( objectToScene["out"] )
		pointInstancer["filter"].setInput( instancerFilter["out"] )

		query = GafferScene.PointInstancerQuery()
		query["scene"].setInput( pointInstancer["out"] )
		query["location"].setValue( "/instancer" )

		for id in range( 1000 ) :

			with self.subTest( id = id ) :

				query["id"].setValue( id )
				self.assertEqual(
					query["attributes"].getValue(),
					IECore.CompoundObject( {
						"attribute" : IECore.Color3fData( imath.Color3f( 1.0 if id % 2 else 0.5 ) ),
					} )
				)
