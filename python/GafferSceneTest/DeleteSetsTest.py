##########################################################################
#
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
import GafferScene
import GafferSceneTest

class DeleteSetsTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		s1 = GafferScene.Set()
		s1["name"].setValue("s1")
		s1["paths"].setValue( IECore.StringVectorData( ["/blah1"] ) )

		s2 = GafferScene.Set()
		s2["name"].setValue("s2")
		s2["in"].setInput( s1["out"] )
		s2["paths"].setValue( IECore.StringVectorData( ["/blah2"] ) )

		s3 = GafferScene.Set()
		s3["name"].setValue("s3")
		s3["in"].setInput( s2["out"] )
		s3["paths"].setValue( IECore.StringVectorData( ["/blah3"] ) )

		d = GafferScene.DeleteSets()
		d["in"].setInput(s3["out"])

		# No sets to delete, so everything should be intact
		self.assertEqual( d["out"]["setNames"].getValue(), IECore.InternedStringVectorData( ['s1','s2','s3'] ) )
		self.assertEqual( d["out"].set( "s1" ).value.paths(), ['/blah1'] )
		self.assertEqual( d["out"].set( "s2" ).value.paths(), ['/blah2'] )
		self.assertEqual( d["out"].set( "s3" ).value.paths(), ['/blah3'] )
		self.assertTrue( d["out"].set( "s1", _copy = False ).isSame( s3["out"].set( "s1", _copy = False ) ) )
		self.assertTrue( d["out"].set( "s2", _copy = False ).isSame( s3["out"].set( "s2", _copy = False ) ) )
		self.assertTrue( d["out"].set( "s3", _copy = False ).isSame( s3["out"].set( "s3", _copy = False ) ) )

		# Delete s1 and s2
		d["names"].setValue( "s1 s2" )
		self.assertEqual( d["out"]["setNames"].getValue(), IECore.InternedStringVectorData( ['s3'] ) )
		self.assertEqual( d["out"].set( "s3" ).value.paths(), ['/blah3'] )
		self.assertTrue( d["out"].set( "s1", _copy = False ).isSame( d["in"]["set"].defaultValue( _copy = False ) ) )
		self.assertTrue( d["out"].set( "s2", _copy = False ).isSame( d["in"]["set"].defaultValue( _copy = False ) ) )
		self.assertTrue( d["out"].set( "s3", _copy = False ).isSame( s3["out"].set( "s3", _copy = False ) ) )

		# Invert
		d["invertNames"].setValue( True )
		self.assertEqual( d["out"]["setNames"].getValue(), IECore.InternedStringVectorData( ['s1','s2' ] ) )
		self.assertEqual( d["out"].set( "s1" ).value.paths(), ['/blah1'] )
		self.assertEqual( d["out"].set( "s2" ).value.paths(), ['/blah2'] )
		self.assertTrue( d["out"].set( "s1", _copy = False ).isSame( d["in"].set( "s1", _copy = False ) ) )
		self.assertTrue( d["out"].set( "s2", _copy = False ).isSame( d["in"].set( "s2", _copy = False ) ) )
		self.assertTrue( d["out"].set( "s3", _copy = False ).isSame( d["in"]["set"].defaultValue( _copy = False ) ) )

	def testWildcards( self ) :

		s1 = GafferScene.Set()
		s1["name"].setValue("a1")

		s2 = GafferScene.Set()
		s2["name"].setValue("a2")
		s2["in"].setInput( s1["out"] )

		s3 = GafferScene.Set()
		s3["name"].setValue("b1")
		s3["in"].setInput( s2["out"] )

		s4 = GafferScene.Set()
		s4["name"].setValue("b2")
		s4["in"].setInput( s3["out"] )

		d = GafferScene.DeleteSets()
		d["in"].setInput(s4["out"])

		self.assertEqual( d["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "a1", "a2", "b1", "b2" ] ) )

		d["names"].setValue( "a*" )
		self.assertEqual( d["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "b1", "b2" ] ) )

		d["names"].setValue( "*1" )
		self.assertEqual( d["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "a2", "b2" ] ) )

		d["names"].setValue( "*1 b2" )
		self.assertEqual( d["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "a2" ] ) )

		d["names"].setValue( "b2 a*" )
		self.assertEqual( d["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "b1" ] ) )

	def testAffects( self ) :

		d = GafferScene.DeleteSets()

		self.assertIn( d["out"]["setNames"], d.affects( d["in"]["setNames"] ) )
		self.assertIn( d["out"]["setNames"], d.affects( d["names"] ) )
		self.assertIn( d["out"]["setNames"], d.affects( d["invertNames"] ) )

	def testWithSetFilter( self ) :

		p = GafferScene.Plane()
		p["sets"].setValue( "test" )

		d = GafferScene.DeleteSets()
		d["in"].setInput( p["out"] )

		f = GafferScene.SetFilter()
		f["setExpression"].setValue( "test" )

		a = GafferScene.CustomAttributes()
		a["in"].setInput( d["out"] )
		a["attributes"].addChild( Gaffer.NameValuePlug( "user:a", 10 ) )
		a["filter"].setInput( f["out"] )

		# We haven't deleted the set yet, so we should get
		# the attribute.
		self.assertTrue( "user:a" in a["out"].attributes( "/plane" ) )

		# Delete the set, and the attribute should go away.
		d["names"].setValue( "test" )
		self.assertFalse( "user:a" in a["out"].attributes( "/plane" ) )

	def testCantDeleteInternalSets( self ) :

		light = GafferSceneTest.TestLight()
		camera = GafferScene.Camera()

		group = GafferScene.Group()
		group["in"][0].setInput( light["out"] )
		group["in"][1].setInput( camera["out"] )

		deleteSets = GafferScene.DeleteSets()
		deleteSets["in"].setInput( group["out"] )
		deleteSets["names"].setValue( "*" )

		self.assertEqual( deleteSets["out"].setNames(), IECore.InternedStringVectorData( [ "__lights", "__cameras" ] ) )
		self.assertEqual( deleteSets["out"].set( "__lights").value.paths(), [ "/group/light" ] )
		self.assertEqual( deleteSets["out"].set( "__cameras").value.paths(), [ "/group/camera" ] )

if __name__ == "__main__":
	unittest.main()
