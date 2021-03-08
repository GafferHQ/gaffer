##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import os
import unittest

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class CustomAttributesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = IECoreScene.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"ball1" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
					"ball2" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
				},
			} )
		)

		a = GafferScene.CustomAttributes()
		a["in"].setInput( input["out"] )

		# should be no attributes until we've specified any
		self.assertEqual( a["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].attributes( "/ball1" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].attributes( "/ball2" ), IECore.CompoundObject() )

		# when we specify some, they should be applied to everything because
		# we haven't specified a filter yet. but not to the root because it
		# isn't allowed attributes.
		a["attributes"].addChild( Gaffer.NameValuePlug( "ri:shadingRate", IECore.FloatData( 0.25 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual( a["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].attributes( "/ball1" ), IECore.CompoundObject( { "ri:shadingRate" : IECore.FloatData( 0.25 ) } ) )
		self.assertEqual( a["out"].attributes( "/ball2" ), IECore.CompoundObject( { "ri:shadingRate" : IECore.FloatData( 0.25 ) } ) )

		# finally once we've applied a filter, we should get some attributes.
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/ball1" ] ) )
		a["filter"].setInput( f["out"] )

		self.assertEqual( a["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].attributes( "/ball1" ), IECore.CompoundObject( { "ri:shadingRate" : IECore.FloatData( 0.25 ) } ) )
		self.assertEqual( a["out"].attributes( "/ball2" ), IECore.CompoundObject() )

	def testOverrideAttributes( self ) :

		sphere = IECoreScene.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"ball1" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
				},
			} )
		)

		a = GafferScene.CustomAttributes()
		a["in"].setInput( input["out"] )

		a["attributes"].addChild( Gaffer.NameValuePlug( "ri:shadingRate", IECore.FloatData( 0.25 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "user:something", IECore.IntData( 1 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual(
			a["out"].attributes( "/ball1" ),
			IECore.CompoundObject( {
				"ri:shadingRate" : IECore.FloatData( 0.25 ),
				"user:something" : IECore.IntData( 1 ),
			} )
		)

		a2 = GafferScene.CustomAttributes()
		a2["in"].setInput( a["out"] )

		self.assertEqual(
			a2["out"].attributes( "/ball1" ),
			IECore.CompoundObject( {
				"ri:shadingRate" : IECore.FloatData( 0.25 ),
				"user:something" : IECore.IntData( 1 ),
			} )
		)

		a2["attributes"].addChild( Gaffer.NameValuePlug( "ri:shadingRate", IECore.FloatData( .5 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		a2["attributes"].addChild( Gaffer.NameValuePlug( "user:somethingElse", IECore.IntData( 10 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		self.assertEqual(
			a2["out"].attributes( "/ball1" ),
			IECore.CompoundObject( {
				"ri:shadingRate" : IECore.FloatData( 0.5 ),
				"user:something" : IECore.IntData( 1 ),
				"user:somethingElse" : IECore.IntData( 10 ),
			} )
		)

	def testHashPassThrough( self ) :

		sphere = IECoreScene.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"ball1" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
					"ball2" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
				},
			} )
		)

		a = GafferScene.CustomAttributes()
		a["in"].setInput( input["out"] )

		# when we have no attributes at all, everything should be a pass-through
		self.assertSceneHashesEqual( input["out"], a["out"] )

		# when we have some attributes, everything except the attributes plug should
		# be a pass-through.
		a["attributes"].addChild( Gaffer.NameValuePlug( "ri:shadingRate", IECore.FloatData( 2.0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertSceneHashesEqual( input["out"], a["out"], checks = self.allSceneChecks - { "attributes" } )
		self.assertSceneHashesNotEqual( input["out"], a["out"], checks = { "attributes" } )

		# when we add a filter, non-matching objects should become pass-throughs
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/ball1" ] ) )
		a["filter"].setInput( f["out"] )
		self.assertSceneHashesEqual( input["out"], a["out"], pathsToPrune = ( "/ball1", ) )

		c = Gaffer.Context()
		c["scene:path"] = IECore.InternedStringVectorData( [ "ball1" ] )
		with c :
			self.assertEqual( a["out"]["childNames"].hash(), input["out"]["childNames"].hash() )
			self.assertEqual( a["out"]["transform"].hash(), input["out"]["transform"].hash() )
			self.assertEqual( a["out"]["bound"].hash(), input["out"]["bound"].hash() )
			self.assertEqual( a["out"]["object"].hash(), input["out"]["object"].hash() )
			self.assertNotEqual( a["out"]["attributes"].hash(), input["out"]["attributes"].hash() )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferScene.CustomAttributes()
		s["a"]["attributes"].addChild( Gaffer.NameValuePlug( "ri:shadingRate", IECore.FloatData( 1.0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["a"]["attributes"] ), 1 )
		self.assertTrue( "attributes1" not in s2["a"] )

	def testBoxPromotion( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferScene.StandardAttributes()
		s["a"]["attributes"]["deformationBlur"]["enabled"].setValue( True )
		s["a"]["attributes"]["deformationBlur"]["value"].setValue( False )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["a"] ] ) )

		self.assertTrue( Gaffer.PlugAlgo.canPromote( b["a"]["attributes"]["deformationBlur"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( b["a"]["attributes"]["deformationBlur"] ) )

		p = Gaffer.PlugAlgo.promote( b["a"]["attributes"]["deformationBlur"] )

		self.assertTrue( Gaffer.PlugAlgo.isPromoted( b["a"]["attributes"]["deformationBlur"] ) )

		self.assertTrue( b["a"]["attributes"]["deformationBlur"].getInput().isSame( p ) )
		self.assertTrue( b["a"]["attributes"]["deformationBlur"]["name"].getInput().isSame( p["name"] ) )
		self.assertTrue( b["a"]["attributes"]["deformationBlur"]["enabled"].getInput().isSame( p["enabled"] ) )
		self.assertTrue( b["a"]["attributes"]["deformationBlur"]["value"].getInput().isSame( p["value"] ) )
		self.assertEqual( p["enabled"].getValue(), True )
		self.assertEqual( p["value"].getValue(), False )

	def testDisconnectDoesntRetainFilterValue( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["f"] = GafferScene.PathFilter()
		s["a"] = GafferScene.CustomAttributes()
		s["a"]["attributes"].addChild( Gaffer.NameValuePlug( "user:test", IECore.IntData( 10 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		self.assertTrue( "user:test" in s["a"]["out"].attributes( "/plane" ) )

		s["a"]["filter"].setInput( s["f"]["out"] )
		self.assertFalse( "user:test" in s["a"]["out"].attributes( "/plane" ) )

		s["a"]["filter"].setInput( None )
		self.assertTrue( "user:test" in s["a"]["out"].attributes( "/plane" ) )

	def testCopyPasteDoesntRetainFilterValue( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["f"] = GafferScene.PathFilter()
		s["a"] = GafferScene.CustomAttributes()
		s["a"]["attributes"].addChild( Gaffer.NameValuePlug( "user:test", IECore.IntData( 10 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		self.assertTrue( "user:test" in s["a"]["out"].attributes( "/plane" ) )

		s["a"]["filter"].setInput( s["f"]["out"] )

		self.assertFalse( "user:test" in s["a"]["out"].attributes( "/plane" ) )

		ss = s.serialise( filter = Gaffer.StandardSet( [ s["p"], s["a"] ] ) )

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertTrue( "f" not in s )
		self.assertTrue( "user:test" in s["a"]["out"].attributes( "/plane" ) )

	def testOutPlugNotSerialised( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferScene.CustomAttributes()

		ss = s.serialise()
		self.assertFalse( "out" in ss )

	def testAffects( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferScene.CustomAttributes()
		p = Gaffer.NameValuePlug( "user:test", 10, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["a"]["attributes"].addChild( p )
		self.assertEqual( set( s["a"].affects( p["value"] ) ), set( [ s["a"]["out"]["attributes"] ] ) )
		self.assertEqual( set( s["a"].affects( s["a"]["extraAttributes"] ) ), set( [ s["a"]["out"]["attributes"] ] ) )

		s["a"]["global"].setValue( True )
		self.assertEqual( set( s["a"].affects( p["value"] ) ), set( [ s["a"]["out"]["globals"] ] ) )
		self.assertEqual( set( s["a"].affects( s["a"]["extraAttributes"] ) ), set( [ s["a"]["out"]["globals"] ] ) )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( """parent["a"]["global"] = context.getFrame() > 10""" )

		self.assertEqual( set( s["a"].affects( p["value"] ) ), set( [ s["a"]["out"]["attributes"], s["a"]["out"]["globals"] ] ) )

	def testExtraAttributes( self ) :

		s = Gaffer.ScriptNode()

		s["sphere"] = GafferScene.Sphere()
		s["a"] = GafferScene.CustomAttributes()
		s["f"] = GafferScene.PathFilter()
		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		s["a"]["filter"].setInput( s["f"]["out"] )
		s["a"]["extraAttributes"].setValue( IECore.CompoundObject( {
			"a1" : IECore.StringData( "from extra" ),
			"a2" : IECore.IntData( 2 ),
		} ) )
		s["a"]["attributes"].addChild(
			Gaffer.NameValuePlug( "a1", IECore.StringData( "from attributes" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		)
		s["a"]["attributes"].addChild(
			Gaffer.NameValuePlug( "a3", IECore.IntData( 5 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		)
		self.assertEqual(
			s["a"]["out"].attributes( "/sphere" ),
			IECore.CompoundObject( {
				"a1" : IECore.StringData( "from extra" ),
				"a2" : IECore.IntData( 2 ),
				"a3" : IECore.IntData( 5 ),
			} )
		)

	def testExtraAttributesOnlyEvaluatedForFilteredLocations( self ) :

		script = Gaffer.ScriptNode()
		script["grid"] = GafferScene.Grid()

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/grid" ] ) )

		script["customAttributes"] = GafferScene.CustomAttributes()
		script["customAttributes"]["in"].setInput( script["grid"]["out"] )
		script["customAttributes"]["filter"].setInput( script["filter"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( """parent["customAttributes"]["extraAttributes"] = IECore.CompoundObject( { "a" : IECore.StringData( str( context.get( "scene:path" ) ) ) } )""" )

		with Gaffer.ContextMonitor( script["expression"] ) as monitor :
			GafferSceneTest.traverseScene( script["customAttributes"]["out"] )

		self.assertEqual( monitor.combinedStatistics().numUniqueValues( "scene:path" ), 1 )

	def testLoadExtraAttributesFrom0_58( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( os.path.join( os.path.dirname( __file__ ), "scripts", "extraAttributes-0.58.5.2.gfr" ) )
		script.load()

		self.assertEqual(
			script["CustomAttributesWithExpression"]["out"].attributes( "/sphere" ),
			IECore.CompoundObject( {
				"a" : IECore.StringData( "a" )
			} )
		)

		self.assertEqual(
			script["CustomAttributesWithValue"]["out"].attributes( "/sphere" ),
			IECore.CompoundObject( {
				"b" : IECore.StringData( "b" )
			} )
		)

		self.assertEqual(
			script["CustomAttributesWithConnection"]["out"].attributes( "/sphere" ),
			IECore.CompoundObject( {
				"c" : IECore.StringData( "c" )
			} )
		)

	def testAssignShader( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["sphereFilter"] = GafferScene.PathFilter()
		script["sphereFilter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		attributes = IECore.CompoundObject( {
			"ai:surface" : IECoreScene.ShaderNetwork( { "output" : IECoreScene.Shader( "flat" ) }, output = "output" )
		} )

		script["attributes"] = GafferScene.CustomAttributes()
		script["attributes"]["in"].setInput( script["sphere"]["out"] )
		script["attributes"]["filter"].setInput( script["sphereFilter"]["out"] )
		script["attributes"]["extraAttributes"].setValue( attributes )
		self.assertEqual( script["attributes"]["out"].attributes( "/sphere" ), attributes )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )
		self.assertEqual( script2["attributes"]["out"].attributes( "/sphere" ), attributes )

	def testDirtyPropagation( self ) :

		attributes = GafferScene.CustomAttributes()
		cs = GafferTest.CapturingSlot( attributes.plugDirtiedSignal() )

		# Adding or removing an attribute should dirty `out.attributes`

		attributes["attributes"].addChild(
			Gaffer.NameValuePlug( "test", 10, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		)
		self.assertIn( attributes["out"]["attributes"], { x[0] for x in cs } )

		del cs[:]
		del attributes["attributes"][0]
		self.assertIn( attributes["out"]["attributes"], { x[0] for x in cs } )

		# And although the Dynamic flag is currently required for proper serialisation
		# of CustomAttributes nodes, its absence shouldn't prevent dirty propagation.
		# We hope to be able to remove the Dynamic flag completely in the future.

		del cs[:]
		attributes["attributes"].addChild( Gaffer.NameValuePlug( "test2", 10 ) )
		self.assertIn( attributes["out"]["attributes"], { x[0] for x in cs } )

		del cs[:]
		del attributes["attributes"][0]
		self.assertIn( attributes["out"]["attributes"], { x[0] for x in cs } )

	def testGlobalsDirtyPropagation( self ) :

		options = GafferScene.StandardOptions()

		attributes = GafferScene.CustomAttributes()
		attributes["in"].setInput( options["out"] )
		attributes["global"].setValue( True )

		self.assertEqual( attributes["out"].globals(), IECore.CompoundObject() )

		cs = GafferTest.CapturingSlot( attributes.plugDirtiedSignal() )
		options["options"]["renderCamera"]["enabled"].setValue( True )

		self.assertIn( attributes["out"]["globals"], { x[0] for x in cs } )
		self.assertEqual( attributes["out"].globals(), IECore.CompoundObject( { "option:render:camera" : IECore.StringData( "" ) } ) )

	def testLoadExtraAttributesFrom0_59( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( os.path.join( os.path.dirname( __file__ ), "scripts", "extraAttributes-0.59.0.0.gfr" ) )
		script.load()

		self.assertEqual(
			script["CustomAttributesWithExpression"]["out"].attributes( "/sphere" ),
			IECore.CompoundObject( {
				"a" : IECore.StringData( "a" )
			} )
		)

		self.assertEqual(
			script["CustomAttributesWithValue"]["out"].attributes( "/sphere" ),
			IECore.CompoundObject( {
				"b" : IECore.StringData( "b" )
			} )
		)

		self.assertEqual(
			script["CustomAttributesWithConnection"]["out"].attributes( "/sphere" ),
			IECore.CompoundObject( {
				"c" : IECore.StringData( "c" )
			} )
		)

	def testCompoundDataExpression( self ) :

		# `testLoadExtraAttributesFrom0_59()` gives us test coverage for loading
		# serialised expressions which assign CompoundData to `extraAttributes`.
		# But it's also possible to create such an expression directly via the
		# API, which is what this test provides coverage for.

		script = Gaffer.ScriptNode()

		script["a"] = GafferScene.CustomAttributes()
		script["e"] = Gaffer.Expression()
		script["e"].setExpression( 'parent["a"]["extraAttributes"] = IECore.CompoundData( { "test" : 10 } )' )

		self.assertEqual(
			script["a"]["extraAttributes"].getValue(),
			IECore.CompoundObject( { "test" : IECore.IntData( 10 ) } )
		)

	def testPlugReordering( self ) :

		sphere = GafferScene.Sphere()
		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		attributes = GafferScene.CustomAttributes()
		attributes["in"].setInput( sphere["out"] )
		attributes["attributes"].addChild(
			Gaffer.NameValuePlug( "test", 10, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		)
		attributes["attributes"].addChild(
			Gaffer.NameValuePlug( "test", 20, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		)
		self.assertEqual( attributes["out"].attributes( "/sphere" )["test"].value, 20 )

		attributes["attributes"].reorderChildren( reversed( attributes["attributes"].children() ) )
		self.assertEqual( attributes["out"].attributes( "/sphere" )["test"].value, 10 )

if __name__ == "__main__":
	unittest.main()
