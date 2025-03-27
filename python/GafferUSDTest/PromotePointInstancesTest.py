##########################################################################
#
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferScene
import GafferSceneTest
import GafferUSD

import IECore
import IECoreScene

import imath

class PromotePointInstancesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ):

		# Basic inputs
		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( i, 0, 0 ) for i in range( 8 ) ] ) )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.StringVectorData( [ "/object/prototypes/cube", "/object/prototypes/sphere" ] ) )
		points["prototypeIndex"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.IntVectorData( [ 0, 0, 0, 0, 1, 1, 1, 1 ] ) )


		def translationMatrix( x ):
			r = imath.M44f()
			r.setTranslation( imath.V3f( x, 0, 0 ) )
			return r

		cube = GafferScene.Cube()
		sphere = GafferScene.Sphere()

		prototypes = GafferScene.Group()
		prototypes["in"][0].setInput( sphere["out"] )
		prototypes["in"][1].setInput( cube["out"] )
		prototypes["name"].setValue( 'prototypes' )



		simpleObjectToScene = GafferScene.ObjectToScene()
		simpleObjectToScene["object"].setValue( points )
		simpleObjectToScene["sets"].setValue( 'usd:pointInstancers' )

		simpleParent = GafferScene.Parent()
		simpleParent["in"].setInput( simpleObjectToScene["out"] )
		simpleParent["parent"].setValue( '/object' )
		simpleParent["children"][0].setInput( prototypes["out"] )

		# Reference scene where we just feed this straight to an adaptor

		referenceAdaptor = GafferUSD._PointInstancerAdaptor()
		referenceAdaptor["in"].setInput( simpleParent["out"] )
		referenceAdaptor["renderer"].setValue( "test" )
		referenceAdaptor["enabledRenderers"].setValue( IECore.StringVectorData( [ "test" ] ) )

		# Do a simple promote, which both tests the basic functionality, and serves as a reference scene for our
		# expected output when we're testing trickier cases

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )

		simplePromotePointInstances = GafferUSD.PromotePointInstances()
		simplePromotePointInstances["in"].setInput( simpleParent["out"] )
		simplePromotePointInstances["filter"].setInput( objectFilter["out"] )
		simplePromotePointInstances["idList"].setValue( IECore.Int64VectorData( [ 2, 3, 5, 7 ] ) )

		simplePromoteAdaptor = GafferUSD._PointInstancerAdaptor()
		simplePromoteAdaptor["in"].setInput( simplePromotePointInstances["out"] )
		simplePromoteAdaptor["renderer"].setValue( "test" )
		simplePromoteAdaptor["enabledRenderers"].setValue( IECore.StringVectorData( [ "test" ] ) )


		self.assertEqual( simplePromotePointInstances["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "object", "promotedInstances" ] ) )
		self.assertEqual( simplePromotePointInstances["out"].childNames( "/promotedInstances" ), IECore.InternedStringVectorData( [ "cube", "sphere" ] ) )
		self.assertEqual( simplePromotePointInstances["out"].childNames( "/promotedInstances/cube" ), IECore.InternedStringVectorData( [ "2", "3" ] ) )
		self.assertEqual( simplePromotePointInstances["out"].object( "/promotedInstances/cube/2" ), cube["out"].object( "/cube" ) )
		self.assertEqual( simplePromotePointInstances["out"].object( "/promotedInstances/cube/3" ), cube["out"].object( "/cube" ) )
		self.assertEqual( simplePromotePointInstances["out"].transform( "/promotedInstances/cube/2" ), translationMatrix( 2 ) )
		self.assertEqual( simplePromotePointInstances["out"].transform( "/promotedInstances/cube/3" ), translationMatrix( 3 ) )
		self.assertEqual( simplePromotePointInstances["out"].childNames( "/promotedInstances/sphere" ), IECore.InternedStringVectorData( [ "5", "7" ] ) )
		self.assertEqual( simplePromotePointInstances["out"].object( "/promotedInstances/sphere/5" ), sphere["out"].object( "/sphere" ) )
		self.assertEqual( simplePromotePointInstances["out"].object( "/promotedInstances/sphere/7" ), sphere["out"].object( "/sphere" ) )
		self.assertEqual( simplePromotePointInstances["out"].transform( "/promotedInstances/cube/5" ), translationMatrix( 5 ) )
		self.assertEqual( simplePromotePointInstances["out"].transform( "/promotedInstances/cube/7" ), translationMatrix( 7 ) )

		# Make sure that we have deactivated correct source ids
		self.assertEqual( simplePromoteAdaptor["out"].childNames( "/object/instances/cube" ), IECore.InternedStringVectorData( [ "0", "1" ] ) )
		self.assertEqual( simplePromoteAdaptor["out"].childNames( "/object/instances/sphere" ), IECore.InternedStringVectorData( [ "4", "6" ] ) )

		# Now lets start testing the corner cases, starting with making sure instanceIds work by reordering the points

		points["P"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( i, 0, 0 ) for i in [ 6, 7, 0, 1, 4, 5, 2, 3 ] ] ) )
		points["prototypeIndex"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.IntVectorData( [ 1, 1, 0, 0, 1, 1, 0, 0 ] ) )
		points["instanceId"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.IntVectorData( [ 6, 7, 0, 1, 4, 5, 2, 3] ) )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )
		objectToScene["sets"].setValue( 'usd:pointInstancers' )

		parent = GafferScene.Parent()
		parent["in"].setInput( objectToScene["out"] )
		parent["parent"].setValue( '/object' )
		parent["children"][0].setInput( prototypes["out"] )

		promoteInstances = GafferUSD.PromotePointInstances()
		promoteInstances["in"].setInput( parent["out"] )
		promoteInstances["filter"].setInput( objectFilter["out"] )
		promoteInstances["enabled"].setValue( False )

		pointInstancerAdaptor = GafferUSD._PointInstancerAdaptor()
		pointInstancerAdaptor["in"].setInput( promoteInstances["out"] )
		pointInstancerAdaptor["renderer"].setValue( "test" )
		pointInstancerAdaptor["enabledRenderers"].setValue( IECore.StringVectorData( [ "test" ] ) )

		# Reordering points should not affect the expanded output
		self.assertScenesEqual( pointInstancerAdaptor["out"], referenceAdaptor["out"] )

		promoteInstances["enabled"].setValue( True )
		promoteInstances["idList"].setValue( IECore.Int64VectorData( [ 2, 3, 5, 7 ] ) )

		self.assertScenesEqual( pointInstancerAdaptor["out"], simplePromoteAdaptor["out"] )

		# Now add bogus ids which are deactivated

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( i, 0, 0 ) for i in [ 6, 7, 0, 1, 0.1, 0.101, 4, 5, 2, 3 ] ] ) )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.StringVectorData( [ "/object/prototypes/cube", "/object/prototypes/sphere" ] ) )
		points["prototypeIndex"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.IntVectorData( [ 1, 1, 0, 0, 0, 0, 1, 1, 0, 0 ] ) )
		points["instanceId"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.IntVectorData( [ 6, 7, 0, 1, 100, 101, 4, 5, 2, 3] ) )
		points["inactiveIds"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.BoolVectorData( [ 0, 0, 0, 0, 1, 1, 0, 0, 0, 0 ] ) )

		objectToScene["object"].setValue( points )

		# This also should have no effect on the expanded output

		promoteInstances["enabled"].setValue( False )

		self.assertScenesEqual( pointInstancerAdaptor["out"], referenceAdaptor["out"] )

		promoteInstances["enabled"].setValue( True )

		self.assertScenesEqual( pointInstancerAdaptor["out"], simplePromoteAdaptor["out"] )

		# Results are the same if inactiveIds is an integer mask
		points["inactiveIds"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.IntVectorData( [ 0, 0, 0, 0, 1, 1, 0, 0, 0, 0 ] ) )

		objectToScene["object"].setValue( points )

		promoteInstances["enabled"].setValue( False )

		self.assertScenesEqual( pointInstancerAdaptor["out"], referenceAdaptor["out"] )

		promoteInstances["enabled"].setValue( True )

		self.assertScenesEqual( pointInstancerAdaptor["out"], simplePromoteAdaptor["out"] )

		# Results are the same if inactiveIds is an idList instead of a mask
		points["inactiveIds"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.Int64VectorData( [ 100, 101 ] ) )

		objectToScene["object"].setValue( points )

		promoteInstances["enabled"].setValue( False )

		self.assertScenesEqual( pointInstancerAdaptor["out"], referenceAdaptor["out"] )

		promoteInstances["enabled"].setValue( True )

		self.assertScenesEqual( pointInstancerAdaptor["out"], simplePromoteAdaptor["out"] )

		# Results are the same if inactiveIds is an int list
		points["inactiveIds"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.IntVectorData( [ 100, 101 ] ) )

		objectToScene["object"].setValue( points )

		promoteInstances["enabled"].setValue( False )

		self.assertScenesEqual( pointInstancerAdaptor["out"], referenceAdaptor["out"] )

		promoteInstances["enabled"].setValue( True )

		self.assertScenesEqual( pointInstancerAdaptor["out"], simplePromoteAdaptor["out"] )

	def testDestination( self ):

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( i, 0, 0 ) for i in range( 8 ) ] ) )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.StringVectorData( [ "/group/object/sphere" ] ) )

		sphere = GafferScene.Sphere()

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )
		objectToScene["sets"].setValue( 'usd:pointInstancers' )

		parent = GafferScene.Parent()
		parent["in"].setInput( objectToScene["out"] )
		parent["parent"].setValue( '/object' )
		parent["children"][0].setInput( sphere["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( parent["out"] )

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ '/group/object' ] ) )

		promotePointInstances = GafferUSD.PromotePointInstances()
		promotePointInstances["in"].setInput( group["out"] )
		promotePointInstances["filter"].setInput( objectFilter["out"] )
		promotePointInstances["idList"].setValue( IECore.Int64VectorData( [ 2, 3, 5, 7 ] ) )

		self.assertEqual( promotePointInstances["out"].childNames( "/group" ), IECore.InternedStringVectorData( ["object", "promotedInstances" ] ) )
		self.assertEqual( promotePointInstances["out"].childNames( "/group/promotedInstances" ), IECore.InternedStringVectorData( ["sphere" ] ) )
		self.assertEqual( promotePointInstances["out"].childNames( "/group/promotedInstances/sphere" ), IECore.InternedStringVectorData( ["2", "3", "5", "7" ] ) )

		promotePointInstances["destination"].setValue( "/testLoc" )
		self.assertEqual( promotePointInstances["out"].childNames( "/" ), IECore.InternedStringVectorData( ["group", "testLoc" ] ) )
		self.assertEqual( promotePointInstances["out"].childNames( "/testLoc/promotedInstances/sphere" ), IECore.InternedStringVectorData( ["2", "3", "5", "7" ] ) )

		promotePointInstances["name"].setValue( "testName" )
		self.assertEqual( promotePointInstances["out"].childNames( "/testLoc" ), IECore.InternedStringVectorData( ["testName" ] ) )
		self.assertEqual( promotePointInstances["out"].childNames( "/testLoc/testName/sphere" ), IECore.InternedStringVectorData( ["2", "3", "5", "7" ] ) )

	def testAttributeTransfer( self ):

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( i, 0, 0 ) for i in range( 8 ) ] ) )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.StringVectorData( [ "/object/sphere" ] ) )

		sphere = GafferScene.Sphere()

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( points )
		objectToScene["sets"].setValue( 'usd:pointInstancers' )

		parent = GafferScene.Parent()
		parent["in"].setInput( objectToScene["out"] )
		parent["parent"].setValue( '/object' )
		parent["children"][0].setInput( sphere["out"] )

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ '/object' ] ) )

		attrs = GafferScene.CustomAttributes()
		attrs["filter"].setInput( objectFilter["out"] )
		attrs["in"].setInput( parent["out"] )
		attrs["attributes"].addChild( Gaffer.NameValuePlug( "foo", Gaffer.StringPlug( "value", defaultValue = 'test' ), True, "member1" ) )

		promotePointInstances = GafferUSD.PromotePointInstances()
		promotePointInstances["in"].setInput( attrs["out"] )
		promotePointInstances["filter"].setInput( objectFilter["out"] )
		promotePointInstances["idList"].setValue( IECore.Int64VectorData( [ 2, 3, 5, 7 ] ) )

		# The attribute on the instancer should be transferred to the newly created promoted group
		self.assertEqual(
			promotePointInstances["out"].attributes( "/promotedInstances" ),
			IECore.CompoundObject({'foo':IECore.StringData( 'test' )})
		)



if __name__ == "__main__":
	unittest.main()
