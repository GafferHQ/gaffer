##########################################################################
#
#  Copyright (c) 2013, John Haddon. All rights reserved.
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
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class TextTest( GafferSceneTest.SceneTestCase ) :

	def testConstruct( self ) :

		t = GafferScene.Text()
		self.assertEqual( t.getName(), "Text" )
		self.assertEqual( t["name"].getValue(), "text" )

	def testCompute( self ) :

		t = GafferScene.Text()

		self.assertEqual( t["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( t["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( t["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "text" ] ) )

		m1 = t["out"].object( "/text" )
		self.assertTrue( isinstance( m1, IECoreScene.MeshPrimitive ) )

		t["text"].setValue( "Hello World 2" )
		m2 = t["out"].object( "/text" )
		self.assertTrue( isinstance( m2, IECoreScene.MeshPrimitive ) )

		self.failUnless( m2.bound().size().x > m1.bound().size().x )

	def testAffects( self ) :

		t = GafferScene.Text()

		s = GafferTest.CapturingSlot( t.plugDirtiedSignal() )

		t["name"].setValue( "ground" )
		self.assertEqual(
			{ x[0] for x in s if not x[0].getName().startswith( "__" ) },
			{ t["name"], t["out"]["childNames"], t["out"]["set"], t["out"] }
		)

		del s[:]
		t["text"].setValue( "cat" )

		self.assertTrue( "out.object" in [ x[0].relativeName( x[0].node() ) for x in s ] )
		self.assertTrue( "out.bound" in [ x[0].relativeName( x[0].node() ) for x in s ] )
		self.assertFalse( "out.childNames" in [ x[0].relativeName( x[0].node() ) for x in s ] )
		self.assertFalse( "out.transform" in [ x[0].relativeName( x[0].node() ) for x in s ] )

		del s[:]
		t["font"].setValue( os.path.expandvars( "$GAFFER_ROOT/fonts/VeraBI.ttf" ) )

		self.assertTrue( "out.object" in [ x[0].relativeName( x[0].node() ) for x in s ] )
		self.assertTrue( "out.bound" in [ x[0].relativeName( x[0].node() ) for x in s ] )
		self.assertFalse( "out.childNames" in [ x[0].relativeName( x[0].node() ) for x in s ] )
		self.assertFalse( "out.transform" in [ x[0].relativeName( x[0].node() ) for x in s ] )

if __name__ == "__main__":
	unittest.main()
