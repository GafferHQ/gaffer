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

class SeedsTest( GafferSceneTest.SceneTestCase ) :
	
	def testChildNames( self ) :
	
		p = GafferScene.Plane()
		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "seeds" )
				
		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "seeds" ] ) )
		self.assertEqual( s["out"].childNames( "/plane/seeds" ), IECore.InternedStringVectorData() )

		s["name"].setValue( "points" )
		
		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "points" ] ) )
		self.assertEqual( s["out"].childNames( "/plane/points" ), IECore.InternedStringVectorData() )
	
	def testObject( self ) :
	
		p = GafferScene.Plane()
		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "seeds" )
		
		self.assertEqual( s["out"].objectHash( "/plane" ), p["out"].objectHash( "/plane" ) )
		self.assertEqual( s["out"].object( "/plane" ), p["out"].object( "/plane" ) )
		
		self.failUnless( isinstance( s["out"].object( "/plane/seeds" ), IECore.PointsPrimitive ) )
		numPoints = s["out"].object( "/plane/seeds" ).numPoints
		
		s["density"].setValue( 10 )
		self.failUnless( s["out"].object( "/plane/seeds" ).numPoints > numPoints )
		
		h = s["out"].objectHash( "/plane/seeds" )
		m = s["out"].object( "/plane/seeds" )
		s["name"].setValue( "notSeeds" )
		self.assertEqual( h, s["out"].objectHash( "/plane/notSeeds" ) )
		self.assertEqual( m, s["out"].object( "/plane/notSeeds" ) )		
		
	def testSceneValidity( self ) :
	
		p = GafferScene.Plane()
		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "seeds" )
		
		self.assertSceneValid( s["out"] )
	
	def testDisabled( self ) :
	
		p = GafferScene.Plane()
		s = GafferScene.Seeds()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "seeds" )
		
		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "seeds" ] ) )
		
		s["enabled"].setValue( False )
		
		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData() )
		self.assertScenesEqual( s["out"], p["out"] )
	
	def testNamePlugDefaultValue( self ) :
	
		s = GafferScene.Seeds()
		self.assertEqual( s["name"].defaultValue(), "seeds" )
		self.assertEqual( s["name"].getValue(), "seeds" )
		 		
if __name__ == "__main__":
	unittest.main()
