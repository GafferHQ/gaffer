##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class SetFilterTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p1 = GafferScene.Plane()
		p2 = GafferScene.Plane()
		g = GafferScene.Group()

		g["in"].setInput( p1["out"] )
		g["in1"].setInput( p2["out"] )

		s = GafferScene.Set()
		s["in"].setInput( g["out"] )
		s["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		f = GafferScene.SetFilter()
		f["set"].setValue( "set" )

		a = GafferScene.StandardAttributes()
		a["in"].setInput( s["out"] )
		a["attributes"]["doubleSided"]["enabled"].setValue( True )
		a["filter"].setInput( f["match"] )

		self.assertSceneValid( a["out"] )

		self.assertTrue( "doubleSided" in a["out"].attributes( "/group/plane" ) )
		self.assertTrue( "doubleSided" not in a["out"].attributes( "/group/plane1" ) )
		self.assertTrue( "doubleSided" not in a["out"].attributes( "/group" ) )

		s["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		self.assertSceneValid( a["out"] )

		self.assertTrue( "doubleSided" not in a["out"].attributes( "/group/plane" ) )
		self.assertTrue( "doubleSided" not in a["out"].attributes( "/group/plane1" ) )
		self.assertTrue( "doubleSided" in a["out"].attributes( "/group" ) )

	def testAffects( self ) :

		p1 = GafferScene.Plane()
		p2 = GafferScene.Plane()
		g = GafferScene.Group()

		g["in"].setInput( p1["out"] )
		g["in1"].setInput( p2["out"] )

		s = GafferScene.Set()
		s["in"].setInput( g["out"] )

		a = GafferScene.StandardAttributes()
		a["in"].setInput( s["out"] )

		# no filter attached - changing a set should affect only
		# the globals.

		cs = GafferTest.CapturingSlot( a.plugDirtiedSignal() )

		s["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		self.assertTrue( a["out"]["globals"] in set( [ c[0] for c in cs ] ) )
		self.assertTrue( a["out"]["attributes"] not in set( [ c[0] for c in cs ] ) )

		# attach a filter - changing a set should affect the
		# attributes too.

		f = GafferScene.SetFilter()
		a["filter"].setInput( f["match"] )

		cs = GafferTest.CapturingSlot( a.plugDirtiedSignal() )

		s["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		self.assertTrue( a["out"]["globals"] in set( [ c[0] for c in cs ] ) )
		self.assertTrue( a["out"]["attributes"] in set( [ c[0] for c in cs ] ) )

	def testMultipleStreams( self ) :

		p1 = GafferScene.Plane()
		g1 = GafferScene.Group()
		g1["in"].setInput( p1["out"] )
		s1 = GafferScene.Set()
		s1["in"].setInput( g1["out"] )
		s1["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		p2 = GafferScene.Plane()
		g2 = GafferScene.Group()
		g2["in"].setInput( p2["out"] )
		s2 = GafferScene.Set()
		s2["in"].setInput( g2["out"] )
		s2["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		f = GafferScene.SetFilter()
		f["set"].setValue( "set" )

		a1 = GafferScene.StandardAttributes()
		a1["in"].setInput( s1["out"] )
		a1["attributes"]["doubleSided"]["enabled"].setValue( True )
		a1["filter"].setInput( f["match"] )

		a2 = GafferScene.StandardAttributes()
		a2["in"].setInput( s2["out"] )
		a2["attributes"]["doubleSided"]["enabled"].setValue( True )
		a2["filter"].setInput( f["match"] )

		self.assertSceneValid( a1["out"] )
		self.assertSceneValid( a2["out"] )

		self.assertTrue( "doubleSided" in a1["out"].attributes( "/group" ) )
		self.assertTrue( "doubleSided" not in a1["out"].attributes( "/group/plane" ) )

		self.assertTrue( "doubleSided" not in a2["out"].attributes( "/group" ) )
		self.assertTrue( "doubleSided" in a2["out"].attributes( "/group/plane" ) )

	def testIsolate( self ) :

		p1 = GafferScene.Plane()
		p2 = GafferScene.Plane()
		g = GafferScene.Group()
		g["in"].setInput( p1["out"] )
		g["in1"].setInput( p2["out"] )

		s1 = GafferScene.Set()
		s1["name"].setValue( "set1" )
		s1["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )
		s1["in"].setInput( g["out"] )

		s2 = GafferScene.Set()
		s2["name"].setValue( "set2" )
		s2["paths"].setValue( IECore.StringVectorData( [ "/group", "/group/plane1" ] ) )
		s2["in"].setInput( s1["out"] )

		f = GafferScene.SetFilter()
		f["set"].setValue( "set1" )

		i = GafferScene.Isolate()
		i["in"].setInput( s2["out"] )
		i["filter"].setInput( f["match"] )

		self.assertSceneValid( i["out"] )
		self.assertEqual( i["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "plane" ] ) )

		sets = i["out"]["globals"].getValue()["gaffer:sets"]
		self.assertEqual( sets["set1"].value.paths(), [ "/group/plane" ] )
		self.assertEqual( sets["set2"].value.paths(), [ "/group" ] )

if __name__ == "__main__":
	unittest.main()
