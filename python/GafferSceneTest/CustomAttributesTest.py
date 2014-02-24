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

import unittest
import threading

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class CustomAttributesTest( GafferSceneTest.SceneTestCase ) :
		
	def test( self ) :
	
		sphere = IECore.SpherePrimitive()
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
		a["attributes"].addMember( "ri:shadingRate", IECore.FloatData( 0.25 ) )
		self.assertEqual( a["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].attributes( "/ball1" ), IECore.CompoundObject( { "ri:shadingRate" : IECore.FloatData( 0.25 ) } ) )
		self.assertEqual( a["out"].attributes( "/ball2" ), IECore.CompoundObject( { "ri:shadingRate" : IECore.FloatData( 0.25 ) } ) )

		# finally once we've applied a filter, we should get some attributes.
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/ball1" ] ) )
		a["filter"].setInput( f["match"] )

		self.assertEqual( a["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].attributes( "/ball1" ), IECore.CompoundObject( { "ri:shadingRate" : IECore.FloatData( 0.25 ) } ) )
		self.assertEqual( a["out"].attributes( "/ball2" ), IECore.CompoundObject() )
	
	def testOverrideAttributes( self ) :
	
		sphere = IECore.SpherePrimitive()
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
		
		a["attributes"].addMember( "ri:shadingRate", IECore.FloatData( 0.25 ) )
		a["attributes"].addMember( "user:something", IECore.IntData( 1 ) )
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
	
		a2["attributes"].addMember( "ri:shadingRate", IECore.FloatData( .5 ) )
		a2["attributes"].addMember( "user:somethingElse", IECore.IntData( 10 ) )
		
		self.assertEqual(
			a2["out"].attributes( "/ball1" ),
			IECore.CompoundObject( {
				"ri:shadingRate" : IECore.FloatData( 0.5 ),
				"user:something" : IECore.IntData( 1 ),
				"user:somethingElse" : IECore.IntData( 10 ),
			} )
		)
	
	def testRendering( self ) :
	
		sphere = IECore.SpherePrimitive()
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
		
		a["attributes"].addMember( "ri:shadingRate", IECore.FloatData( 0.25 ) )
		a["attributes"].addMember( "user:something", IECore.IntData( 1 ) )
		
		r = IECore.CapturingRenderer()
		with IECore.WorldBlock( r ) :
			r.procedural( GafferScene.SceneProcedural( a["out"], Gaffer.Context(), "/" ) )
			
		g = r.world()
		attributes = g.children()[0].children()[0].children()[0].children()[0].state()[0]
		self.assertEqual(
			attributes.attributes,
			IECore.CompoundData( {
				"name" : IECore.StringData( "/ball1" ),
				"ri:shadingRate" : IECore.FloatData( 0.25 ),
				"user:something" : IECore.IntData( 1 ),
			} )
		)
	
	def testHashPassThrough( self ) :
		
		sphere = IECore.SpherePrimitive()
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
		a["attributes"].addMember( "ri:shadingRate", IECore.FloatData( 2.0 ) )
		self.assertSceneHashesEqual( input["out"], a["out"], childPlugNames = ( "globals", "childNames", "transform", "bound", "object" ) )
		self.assertSceneHashesNotEqual( input["out"], a["out"], childPlugNames = ( "attributes", ) )
		
		# when we add a filter, non-matching objects should become pass-throughs
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/ball1" ] ) )
		a["filter"].setInput( f["match"] )
		self.assertSceneHashesEqual( input["out"], a["out"], pathsToIgnore = ( "/ball1", ) )
		
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
		s["a"]["attributes"].addMember( "ri:shadingRate", IECore.FloatData( 1.0 ) )

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

		self.assertTrue( b.canPromotePlug( b["a"]["attributes"]["deformationBlur"] ) )
		self.assertFalse( b.plugIsPromoted( b["a"]["attributes"]["deformationBlur"] ) )

		p = b.promotePlug( b["a"]["attributes"]["deformationBlur"] )

		self.assertTrue( b.plugIsPromoted( b["a"]["attributes"]["deformationBlur"] ) )

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
		s["a"]["attributes"].addMember( "user:test", IECore.IntData( 10 ) )
		
		self.assertTrue( "user:test" in s["a"]["out"].attributes( "/plane" ) )

		s["a"]["filter"].setInput( s["f"]["match"] )
		self.assertFalse( "user:test" in s["a"]["out"].attributes( "/plane" ) )

		s["a"]["filter"].setInput( None )
		self.assertTrue( "user:test" in s["a"]["out"].attributes( "/plane" ) )

	def testCopyPasteDoesntRetainFilterValue( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["p"] = GafferScene.Plane()
		s["f"] = GafferScene.PathFilter()
		s["a"] = GafferScene.CustomAttributes()
		s["a"]["attributes"].addMember( "user:test", IECore.IntData( 10 ) )
		
		self.assertTrue( "user:test" in s["a"]["out"].attributes( "/plane" ) )

		s["a"]["filter"].setInput( s["f"]["match"] )

		self.assertFalse( "user:test" in s["a"]["out"].attributes( "/plane" ) )

		ss = s.serialise( filter = Gaffer.StandardSet( [ s["p"], s["a"] ] ) )
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertTrue( "f" not in s )
		self.assertTrue( "user:test" in s["a"]["out"].attributes( "/plane" ) )

if __name__ == "__main__":
	unittest.main()
