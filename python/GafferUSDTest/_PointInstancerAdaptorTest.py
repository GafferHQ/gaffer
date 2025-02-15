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

class _PointInstancerAdaptorTest( GafferSceneTest.SceneTestCase ) :

	def testBasic( self ):

		cube = GafferScene.Cube()

		cubeFilter = GafferScene.PathFilter()
		cubeFilter["paths"].setValue( IECore.StringVectorData( [ '/cube' ] ) )

		prototypeRootsTweaks = GafferScene.PrimitiveVariableTweaks()
		prototypeRootsTweaks["tweaks"].addChild( Gaffer.TweakPlug( Gaffer.StringVectorDataPlug( "value", defaultValue = IECore.StringVectorData( [ '/cube/prototypes/sphere' ] ) ), "tweak0" ) )
		prototypeRootsTweaks["in"].setInput( cube["out"] )
		prototypeRootsTweaks["filter"].setInput( cubeFilter["out"] )
		prototypeRootsTweaks["interpolation"].setValue( 1 )
		prototypeRootsTweaks["tweaks"]["tweak0"]["name"].setValue( 'prototypeRoots' )
		prototypeRootsTweaks["tweaks"]["tweak0"]["mode"].setValue( 5 )

		pointInstancerSet = GafferScene.Set()
		pointInstancerSet["in"].setInput( prototypeRootsTweaks["out"] )
		pointInstancerSet["filter"].setInput( cubeFilter["out"] )
		pointInstancerSet["name"].setValue( 'usd:pointInstancers' )

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( pointInstancerSet["out"] )
		customAttributes["filter"].setInput( cubeFilter["out"] )

		sphere = GafferScene.Sphere()

		prototypes = GafferScene.Group()
		prototypes["in"][0].setInput( sphere["out"] )
		prototypes["name"].setValue( 'prototypes' )

		parent = GafferScene.Parent()
		parent["in"].setInput( customAttributes["out"] )
		parent["parent"].setValue( '/cube' )
		parent["children"][0].setInput( prototypes["out"] )

		pointInstancerAdaptor = GafferUSD._PointInstancerAdaptor()
		pointInstancerAdaptor["in"].setInput( parent["out"] )

		self.assertEqual(
			pointInstancerAdaptor["out"].childNames( "/cube" ),
			IECore.InternedStringVectorData( [ "prototypes", "instances" ] )
		)
		# Prototypes are hidden
		self.assertEqual(
			pointInstancerAdaptor["out"].attributes( "/cube/prototypes" ),
			IECore.CompoundObject( { 'scene:visible':IECore.BoolData( 0 ) } )
		)

		# Instances are expanded
		self.assertEqual(
			pointInstancerAdaptor["out"].object( "/cube/instances" ),
			IECore.NullObject()
		)
		self.assertEqual(
			pointInstancerAdaptor["out"].childNames( "/cube/instances" ),
			IECore.InternedStringVectorData( [ "sphere" ] )
		)
		self.assertEqual(
			pointInstancerAdaptor["out"].childNames( "/cube/instances/sphere" ),
			IECore.InternedStringVectorData( [ str( i ) for i in range( 8 ) ] )
		)
		for i in range( 8 ):
			self.assertEqual(
				pointInstancerAdaptor["out"].object( "/cube/instances/sphere/%i" % i ),
				sphere["out"].object( "/sphere" )
			)
		self.assertSceneValid( pointInstancerAdaptor["out"] )

		# Instances are encapsulated when rendering to Arnold
		pointInstancerAdaptor["renderer"].setValue( "Arnold" )
		self.assertEqual(
			pointInstancerAdaptor["out"].childNames( "/cube/instances" ),
			IECore.InternedStringVectorData( [] )
		)
		self.assertEqual( type( pointInstancerAdaptor["out"].object( "/cube/instances" ) ), GafferScene.Capsule )

		# This parameter controls the default for whether locations get processed, based on the chosen renderer
		pointInstancerAdaptor["defaultEnabledPerRenderer"].setValue( { "Arnold" : False } )
		self.assertScenesEqual( pointInstancerAdaptor["out"], pointInstancerAdaptor["in"] )

		# The attribute can override
		customAttributes["attributes"].addChild( Gaffer.NameValuePlug( "gafferUSD:pointInstancerAdaptor:enabled", Gaffer.BoolPlug( "value", defaultValue = True ), True, "member1" ) )

		self.assertEqual( type( pointInstancerAdaptor["out"].object( "/cube/instances" ) ), GafferScene.Capsule )

		pointInstancerAdaptor["defaultEnabledPerRenderer"].setValue( { "Arnold" : True } )

		self.assertEqual( type( pointInstancerAdaptor["out"].object( "/cube/instances" ) ), GafferScene.Capsule )

		customAttributes["attributes"]["member1"]["value"].setValue( False )

		self.assertScenesEqual( pointInstancerAdaptor["out"], pointInstancerAdaptor["in"] )


	def testRecursiveUSD( self ):

		# Test with a scene where some prototypes are also instancers - all levels should get expanded
		sceneReader = GafferScene.SceneReader()
		sceneReader["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/usdFiles/recursiveInst.usda" )

		pointInstancerAdaptor = GafferUSD._PointInstancerAdaptor()
		pointInstancerAdaptor["in"].setInput( sceneReader["out"] )

		self.assertSceneValid( pointInstancerAdaptor["out"] )
		self.assertEqual(
			pointInstancerAdaptor["out"].childNames( "/inst" ),
			IECore.InternedStringVectorData( [ "Prototypes", "instances" ] )
		)
		self.assertEqual(
			pointInstancerAdaptor["out"].attributes( "/inst/Prototypes" )[ 'scene:visible'],
			IECore.BoolData( 0 )
		)
		self.assertEqual(
			pointInstancerAdaptor["out"].childNames( "/inst/instances" ),
			IECore.InternedStringVectorData( [ "sphere", "subInst" ] )
		)
		self.assertEqual(
			pointInstancerAdaptor["out"].childNames( "/inst/instances/sphere" ),
			IECore.InternedStringVectorData( [ "1", "3", "5", "7", "9" ] )
		)
		for i in [ "1", "3", "5", "7", "9" ]:
			self.assertEqual(
				pointInstancerAdaptor["out"].object( "/inst/instances/sphere/" + i ),
				IECoreScene.SpherePrimitive()
			)
		self.assertEqual(
			pointInstancerAdaptor["out"].childNames( "/inst/instances/subInst" ),
			IECore.InternedStringVectorData( [ "0", "2", "4", "6", "8" ] )
		)
		for i in [ "0", "2", "4", "6", "8" ]:
			self.assertEqual(
				pointInstancerAdaptor["out"].childNames( "/inst/instances/subInst/" + i ),
				IECore.InternedStringVectorData( [ "Prototypes", "instances" ] )
			)
			self.assertEqual(
				pointInstancerAdaptor["out"].attributes( "/inst/instances/subInst/%s/Prototypes"%i )[ 'scene:visible'],
				IECore.BoolData( 0 )
			)
			self.assertEqual(
				pointInstancerAdaptor["out"].childNames( "/inst/instances/subInst/%s/instances"%i ),
				IECore.InternedStringVectorData( [ "sphere" ] )
			)
			self.assertEqual(
				pointInstancerAdaptor["out"].childNames( "/inst/instances/subInst/%s/instances/sphere"%i ),
				IECore.InternedStringVectorData( [ str(j) for j in [ 0, 1, 2, 5, 6, 7, 8, 9 ] ] )
			)
			for j in [ 0, 1, 2, 5, 6, 7, 8, 9 ]:
				self.assertEqual(
					pointInstancerAdaptor["out"].object( "/inst/instances/subInst/%s/instances/sphere/%i"%(i,j) ),
					IECoreScene.SpherePrimitive( 0.3 )
				)

		pointInstancerAdaptorEncapsulating = GafferUSD._PointInstancerAdaptor()
		pointInstancerAdaptorEncapsulating["in"].setInput( sceneReader["out"] )
		pointInstancerAdaptorEncapsulating["renderer"].setValue( "Arnold" )

		self.assertEqual( type( pointInstancerAdaptorEncapsulating["out"].object( "/inst/instances" ) ), GafferScene.Capsule )
		self.assertScenesRenderSame( pointInstancerAdaptor["out"], pointInstancerAdaptorEncapsulating["out"], expandProcedurals = True, ignoreLinks = True )

	def testRelativePrototypes( self ):

		# Since we've tested with this scene above, and know it works, we can use it to validate how we handle
		# relative prototypes
		sceneReader = GafferScene.SceneReader()
		sceneReader["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/usdFiles/recursiveInst.usda" )

		pointInstancerAdaptor = GafferUSD._PointInstancerAdaptor()
		pointInstancerAdaptor["in"].setInput( sceneReader["out"] )
		pointInstancerAdaptor["renderer"].setValue( "Arnold" )

		postGroup = GafferScene.Group()
		postGroup["transform"]["rotate"]["x"].setValue( 30 )
		postGroup["in"][0].setInput( pointInstancerAdaptor["out"] )

		preGroup = GafferScene.Group()
		preGroup["transform"]["rotate"]["x"].setValue( 30 )
		preGroup["in"][0].setInput( sceneReader["out"] )

		pointInstancerAdaptorAfterGroup = GafferUSD._PointInstancerAdaptor()
		pointInstancerAdaptorAfterGroup["in"].setInput( preGroup["out"] )
		pointInstancerAdaptorAfterGroup["renderer"].setValue( "Arnold" )

		self.assertScenesRenderSame( postGroup["out"], pointInstancerAdaptorAfterGroup["out"], expandProcedurals = True, ignoreLinks = True )

		# It would be nice if these capsules would hash the same, but they don't, because the global sets are
		# different between these two setups. Instead, in order to demonstrate getting matching hashes when
		# the same instancing is performed at different points in the hierarchy, we need to construct a scene
		# with both instancers at once, so the sets will match.
		self.assertNotEqual(
			pointInstancerAdaptorAfterGroup["out"].object( "/group/inst/instances" ).hash(),
			pointInstancerAdaptor["out"].object( "/inst/instances" ).hash()
		)

		refMerge = GafferScene.Parent()
		refMerge["parent"].setValue( "/" )
		refMerge["in"].setInput( pointInstancerAdaptor["out"] )
		refMerge["children"][0].setInput( pointInstancerAdaptorAfterGroup["out"] )

		preMerge = GafferScene.Parent()
		preMerge["parent"].setValue( "/" )
		preMerge["in"].setInput( sceneReader["out"] )
		preMerge["children"][0].setInput( preGroup["out"] )

		pointInstancerAdaptorAfterMerge = GafferUSD._PointInstancerAdaptor()
		pointInstancerAdaptorAfterMerge["in"].setInput( preMerge["out"] )
		pointInstancerAdaptorAfterMerge["renderer"].setValue( "Arnold" )

		self.assertScenesRenderSame( pointInstancerAdaptorAfterMerge["out"], refMerge["out"], expandProcedurals = True, ignoreLinks = True )

		# Make sure that the same source, placed at different points in the hierarchy, results in a capsule
		# with the same hash, so that the renderer will instance these capsules properly.
		self.assertEqual(
			pointInstancerAdaptorAfterMerge["out"].object( "/inst/instances" ).hash(),
			pointInstancerAdaptorAfterMerge["out"].object( "/group/inst/instances" ).hash()
		)


	def testNullObjectInInstancerSet( self ):
		# If the user has applied an Instancer node of their own, there may be locations that are tagged as being
		# in the usd:pointInstancers set, but don't have a point cloud object there. We want to ignore these
		# locations - we don't want to output empty capsules, and we don't want to hide the children of these
		# fake instancers ( the children are probably the actual instances, expanded by the user )

		subGroup = GafferScene.Group()

		group = GafferScene.Group()
		group["in"][0].setInput( subGroup["out"] )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ '/group' ] ) )

		pointInstancerSet = GafferScene.Set()
		pointInstancerSet["in"].setInput( group["out"] )
		pointInstancerSet["filter"].setInput( groupFilter["out"] )
		pointInstancerSet["name"].setValue( 'usd:pointInstancers' )

		pointInstancerAdaptor = GafferUSD._PointInstancerAdaptor()
		pointInstancerAdaptor["in"].setInput( pointInstancerSet["out"] )

		# We're not making the children invisible
		self.assertEqual( pointInstancerAdaptor["out"].attributes( "/group/group" ), IECore.CompoundObject() )
		# And not adding child locations
		self.assertEqual( pointInstancerAdaptor["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "group" ] ) )
		# In fact, we're not changing anything
		self.assertScenesEqual( pointInstancerAdaptor["out"], pointInstancerAdaptor["in"] )

		# Special test that we aren't making any empty capsules from this empty object, because that
		# triggers Arnold warnings
		pointInstancerAdaptor["renderer"].setValue( "Arnold" )

		self.assertScenesEqual( pointInstancerAdaptor["out"], pointInstancerAdaptor["in"] )

if __name__ == "__main__":
	unittest.main()
