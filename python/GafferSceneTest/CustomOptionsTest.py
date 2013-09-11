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

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class CustomOptionsTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :
	
		p = GafferScene.Plane()
		options = GafferScene.CustomOptions()
		options["in"].setInput( p["out"] )
	
		# check that the scene hierarchy is passed through
	
		self.assertEqual( options["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( options["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( options["out"].bound( "/" ), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( options["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )
		
		self.assertEqual( options["out"].object( "/plane" ), IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -0.5 ), IECore.V2f( 0.5 ) ) ) )
		self.assertEqual( options["out"].transform( "/plane" ), IECore.M44f() )
		self.assertEqual( options["out"].bound( "/plane" ), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( options["out"].childNames( "/plane" ), IECore.InternedStringVectorData() )
		
		# check that we have some displays
		
		options["options"].addMember( "test", IECore.IntData( 10 ) )
		options["options"].addMember( "test2", IECore.StringData( "10" ) )
		
		g = options["out"]["globals"].getValue()
		self.assertEqual( len( g ), 2 )
		self.assertEqual( g["test"], IECore.IntData( 10 ) )
		self.assertEqual( g["test2"], IECore.StringData( "10" ) )
	
	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["optionsNode"] = GafferScene.CustomOptions()
		s["optionsNode"]["options"].addMember( "test", IECore.IntData( 10 ) )
		s["optionsNode"]["options"].addMember( "test2", IECore.StringData( "10" ) )
		
		ss = s.serialise()
		
		s2 = Gaffer.ScriptNode()		
		s2.execute( ss )
		
		g = s2["optionsNode"]["out"]["globals"].getValue()
		self.assertEqual( len( g ), 2 )
		self.assertEqual( g["test"], IECore.IntData( 10 ) )
		self.assertEqual( g["test2"], IECore.StringData( "10" ) )
		self.assertTrue( "options1" not in s2["optionsNode"] )
	
	def testHashPassThrough( self ) :
	
		# the hash of the per-object part of the output should be
		# identical to the input, so that they share cache entries.
	
		p = GafferScene.Plane()
		options = GafferScene.CustomOptions()
		options["in"].setInput( p["out"] )
		options["options"].addMember( "test", IECore.IntData( 10 ) )
		
		self.assertSceneHashesEqual( p["out"], options["out"], childPlugNames = ( "transform", "bound", "attributes", "object", "childNames" ) )
	
	def testDisabled( self ) :
	
		p = GafferScene.Plane()
		options = GafferScene.CustomOptions()
		options["in"].setInput( p["out"] )
		options["options"].addMember( "test", IECore.IntData( 10 ) )
	
		self.assertSceneHashesEqual( p["out"], options["out"], childPlugNames = ( "transform", "bound", "attributes", "object", "childNames" ) )
		self.assertNotEqual( options["out"]["globals"].hash(), p["out"]["globals"].hash() )
		
		options["enabled"].setValue( False )
		
		self.assertSceneHashesEqual( p["out"], options["out"] )
		self.assertScenesEqual( p["out"], options["out"] )
	
	def testDirtyPropagation( self ) :
	
		p = GafferScene.Plane()
		o = GafferScene.CustomOptions()
		
		o["in"].setInput( p["out"] )
		
		cs = GafferTest.CapturingSlot( o.plugDirtiedSignal() )
		
		p["dimensions"]["x"].setValue( 100.1 )
		
		dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )
		
		self.assertEqual( len( dirtiedPlugs ), 6 )
		self.assertTrue( "in.bound" in dirtiedPlugs )
		self.assertTrue( "in.object" in dirtiedPlugs )
		self.assertTrue( "in" in dirtiedPlugs )
		self.assertTrue( "out.bound" in dirtiedPlugs )
		self.assertTrue( "out.object" in dirtiedPlugs )
		self.assertTrue( "out" in dirtiedPlugs )
		
if __name__ == "__main__":
	unittest.main()
