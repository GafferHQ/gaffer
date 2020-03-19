##########################################################################
#
#  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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
import GafferSceneTest

class ShuffleAttributesTest( GafferSceneTest.SceneTestCase ) :

	def testShuffles( self ) :

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( cube["out"] )
		mainAttrs = GafferScene.CustomAttributes()
		mainAttrs["in"].setInput( group["out"] )
		mainAttrs["attributes"].addChild( Gaffer.NameValuePlug( "foo", 0.5 ) )
		mainAttrs["attributes"].addChild( Gaffer.NameValuePlug( "bar", 1.0 ) )
		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		mainAttrs["filter"].setInput( groupFilter["out"] )
		sphereAttrs = GafferScene.CustomAttributes()
		sphereAttrs["in"].setInput( mainAttrs["out"] )
		sphereAttrs["attributes"].addChild( Gaffer.NameValuePlug( "foo", 1.5 ) )
		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		sphereAttrs["filter"].setInput( sphereFilter["out"] )
		groupShuffles = GafferScene.ShuffleAttributes()
		groupShuffles["filter"].setInput( groupFilter["out"] )
		groupShuffles["in"].setInput( sphereAttrs["out"] )
		groupShuffles["shuffles"].addChild( Gaffer.ShufflePlug() )

		def assertResults( node, groupResults, sphereResults ) :

			self.assertEqual( node["out"].attributes( "/group" ), groupResults )

			self.assertEqual( node["out"].attributes( "/group/cube" ), IECore.CompoundObject() )
			self.assertEqual( node["out"].fullAttributes( "/group/cube" ), groupResults )

			combinedResults = groupResults.copy()
			combinedResults.update( sphereResults )
			self.assertEqual( node["out"].attributes( "/group/sphere" ), sphereResults )
			self.assertEqual( node["out"].fullAttributes( "/group/sphere" ), combinedResults )

		# no-op with no valid shuffles
		assertResults(
			node = groupShuffles,
			groupResults = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ), } ),
			sphereResults = IECore.CompoundObject( { "foo" : IECore.FloatData( 1.5 ), } )
		)

		# copy foo to baz
		groupShuffles["shuffles"][0]["source"].setValue( "foo" )
		groupShuffles["shuffles"][0]["destination"].setValue( "baz" )
		assertResults(
			node = groupShuffles,
			groupResults = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ), "baz" : IECore.FloatData( 0.5 ), } ),
			sphereResults = IECore.CompoundObject( { "foo" : IECore.FloatData( 1.5 ), } )
		)

		# move foo to baz
		groupShuffles["shuffles"][0]["deleteSource"].setValue( True )
		assertResults(
			node = groupShuffles,
			groupResults = IECore.CompoundObject( { "bar" : IECore.FloatData( 1.0 ), "baz" : IECore.FloatData( 0.5 ), } ),
			sphereResults = IECore.CompoundObject( { "foo" : IECore.FloatData( 1.5 ), } )
		)

		sphereShuffles = GafferScene.ShuffleAttributes()
		sphereShuffles["in"].setInput( groupShuffles["out"] )
		sphereShuffles["filter"].setInput( sphereFilter["out"] )
		sphereShuffles["shuffles"].addChild( Gaffer.ShufflePlug() )

		# inherited attrs can't be shuffled
		sphereShuffles["shuffles"][0]["source"].setValue( "bar" )
		sphereShuffles["shuffles"][0]["destination"].setValue( "${source}:bongo" )
		assertResults(
			node = sphereShuffles,
			groupResults = IECore.CompoundObject( { "bar" : IECore.FloatData( 1.0 ), "baz" : IECore.FloatData( 0.5 ), } ),
			sphereResults = IECore.CompoundObject( { "foo" : IECore.FloatData( 1.5 ), } )
		)

		# inherited attrs can't be deleted (ie. /group/sphere fullAttributes will still contain foo)
		groupShuffles["shuffles"][0]["deleteSource"].setValue( False )
		sphereShuffles["shuffles"][0]["source"].setValue( "foo" )
		sphereShuffles["shuffles"][0]["destination"].setValue( "${source}:bongo" )
		sphereShuffles["shuffles"][0]["deleteSource"].setValue( True )
		assertResults(
			node = sphereShuffles,
			groupResults = IECore.CompoundObject( { "foo" : IECore.FloatData( 0.5 ), "bar" : IECore.FloatData( 1.0 ), "baz" : IECore.FloatData( 0.5 ), } ),
			sphereResults = IECore.CompoundObject( { "foo:bongo" : IECore.FloatData( 1.5 ), } )
		)

	def testExpressions( self ) :

		script = Gaffer.ScriptNode()
		script["sphere"] = GafferScene.Sphere()
		script["attrs"] = GafferScene.CustomAttributes()
		script["attrs"]["in"].setInput( script["sphere"]["out"] )
		script["attrs"]["attributes"].addChild( Gaffer.NameValuePlug( "foo", 0.5, True ) )
		script["attrs"]["attributes"].addChild( Gaffer.NameValuePlug( "baz", 1.0, True ) )
		script["sphereFilter"] = GafferScene.PathFilter()
		script["sphereFilter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		script["attrs"]["filter"].setInput( script["sphereFilter"]["out"] )
		script["shuffles"] = GafferScene.ShuffleAttributes()
		script["shuffles"]["filter"].setInput( script["sphereFilter"]["out"] )
		script["shuffles"]["in"].setInput( script["attrs"]["out"] )
		script["shuffles"]["shuffles"].addChild( Gaffer.ShufflePlug( "*", "", deleteSource = True ) )
		script["expr"] = Gaffer.Expression()
		script["expr"].setExpression( 'parent["shuffles"]["shuffles"]["shuffle"]["destination"] = context["source"] + ":bar"' )

		self.assertEqual(
			script["shuffles"]["out"].attributes( "/sphere" ),
			IECore.CompoundObject( { "foo:bar" : IECore.FloatData( 0.5 ), "baz:bar" : IECore.FloatData( 1 ) } )
		)

		# rename an attribute
		script["attrs"]["attributes"][1]["name"].setValue( "bongo" )
		self.assertEqual(
			script["shuffles"]["out"].attributes( "/sphere" ),
			IECore.CompoundObject( { "foo:bar" : IECore.FloatData( 0.5 ), "bongo:bar" : IECore.FloatData( 1 ) } )
		)

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferScene.ShuffleAttributes()
		s["a"]["shuffles"].addChild( Gaffer.ShufflePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["a"]["shuffles"][0]["source"].setValue( "foo" )
		s["a"]["shuffles"][0]["destination"].setValue( "bar" )
		s["a"]["shuffles"][0]["enabled"].setValue( False )
		s["a"]["shuffles"][0]["deleteSource"].setValue( True )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len(s2["a"]["shuffles"].children()), 1 )
		self.assertEqual( s2["a"]["shuffles"][0]["source"].getValue(), "foo" )
		self.assertEqual( s2["a"]["shuffles"][0]["source"].defaultValue(), "" )
		self.assertEqual( s2["a"]["shuffles"][0]["destination"].getValue(), "bar" )
		self.assertEqual( s2["a"]["shuffles"][0]["destination"].defaultValue(), "" )
		self.assertEqual( s2["a"]["shuffles"][0]["enabled"].getValue(), False )
		self.assertEqual( s2["a"]["shuffles"][0]["enabled"].defaultValue(), True )
		self.assertEqual( s2["a"]["shuffles"][0]["deleteSource"].getValue(), True )
		self.assertEqual( s2["a"]["shuffles"][0]["deleteSource"].defaultValue(), False )

	def testPassThroughs( self ) :

		p = GafferScene.Plane()
		p["sets"].setValue( "flatThings" )

		a = GafferScene.ShuffleAttributes()
		a["in"].setInput( p["out"] )

		self.assertEqual( a["out"]["setNames"].hash(), p["out"]["setNames"].hash() )
		self.assertEqual( a["out"].setHash( "flatThings" ), p["out"].setHash( "flatThings" ) )
		self.assertTrue( a["out"].set( "flatThings", _copy=False ).isSame( p["out"].set( "flatThings", _copy=False ) ) )

		self.assertEqual( a["out"]["globals"].hash(), p["out"]["globals"].hash() )
		self.assertEqual( a["out"].globalsHash(), p["out"].globalsHash() )
		self.assertTrue( a["out"].globals( _copy=False ).isSame( p["out"].globals( _copy=False ) ) )

	def assertPromotedAttribute( self, script ) :

		self.assertIn( "shuffles_shuffle0", script["b"] )
		self.assertIsInstance( script["b"]["shuffles_shuffle0"], Gaffer.ShufflePlug )

		self.assertIn( "source", script["b"]["shuffles_shuffle0"] )
		self.assertIsInstance( script["b"]["shuffles_shuffle0"]["source"], Gaffer.StringPlug )

		self.assertIn( "destination", script["b"]["shuffles_shuffle0"] )
		self.assertIsInstance( script["b"]["shuffles_shuffle0"]["destination"], Gaffer.StringPlug )

		self.assertIn( "enabled", script["b"]["shuffles_shuffle0"] )
		self.assertIsInstance( script["b"]["shuffles_shuffle0"]["enabled"], Gaffer.BoolPlug )

		self.assertIn( "deleteSource", script["b"]["shuffles_shuffle0"] )
		self.assertIsInstance( script["b"]["shuffles_shuffle0"]["deleteSource"], Gaffer.BoolPlug )

		self.assertTrue( Gaffer.PlugAlgo.isPromoted( script["b"]["a"]["shuffles"][0] ) )
		self.assertEqual(
			script["b"]["a"]["shuffles"][0].getInput(),
			script["b"]["shuffles_shuffle0"]
		)

		self.assertTrue( script["b"]["shuffles_shuffle0"].getFlags( Gaffer.Plug.Flags.Dynamic ) )

	def testPromoteAndSerialiseAttribute( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferScene.ShuffleAttributes()
		s["b"]["a"]["shuffles"].addChild( Gaffer.ShufflePlug( "shuffle0", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		Gaffer.PlugAlgo.promote( s["b"]["a"]["shuffles"][0] )
		self.assertPromotedAttribute( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertPromotedAttribute( s2 )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )
		self.assertPromotedAttribute( s3 )

if __name__ == "__main__":
	unittest.main()
