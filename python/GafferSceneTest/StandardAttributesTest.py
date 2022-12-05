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

import pathlib

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class StandardAttributesTest( GafferSceneTest.SceneTestCase ) :

	def testDefaultValues( self ) :

		s = GafferScene.StandardAttributes()

		self.assertEqual( s["attributes"]["visibility"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["doubleSided"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["transformBlur"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["transformBlurSegments"]["value"].getValue(), 1 )
		self.assertEqual( s["attributes"]["deformationBlur"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["deformationBlurSegments"]["value"].getValue(), 1 )
		self.assertEqual( s["attributes"]["linkedLights"]["value"].getValue(), "" )

		self.assertEqual( s["attributes"]["visibility"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["doubleSided"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["transformBlur"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["transformBlurSegments"]["value"].defaultValue(), 1 )
		self.assertEqual( s["attributes"]["deformationBlur"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["deformationBlurSegments"]["value"].defaultValue(), 1 )
		self.assertEqual( s["attributes"]["linkedLights"]["value"].defaultValue(), "" )

	def testSerialisationWithInvisibility( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferScene.StandardAttributes()
		s["a"]["attributes"]["visibility"]["value"].setValue( False )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["a"]["attributes"]["visibility"]["value"].getValue(), False )
		self.assertEqual( s2["a"]["attributes"]["visibility"]["value"].defaultValue(), True )

	def testGlobal( self ) :

		p = GafferScene.Plane()
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		a = GafferScene.StandardAttributes()
		a["in"].setInput( p["out"] )
		a["filter"].setInput( f["out"] )
		a["attributes"]["transformBlurSegments"]["enabled"].setValue( True )
		a["attributes"]["transformBlurSegments"]["value"].setValue( 2 )

		self.assertEqual( a["out"].attributes( "/plane" )["gaffer:transformBlurSegments"], IECore.IntData( 2 ) )
		self.assertEqual( a["out"]["globals"].hash(), a["in"]["globals"].hash() )
		self.assertEqual( a["out"]["globals"].getValue(), a["in"]["globals"].getValue() )

		a["global"].setValue( True )

		self.assertEqual( a["out"].attributes( "/plane" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].attributesHash( "/plane" ), a["in"].attributesHash( "/plane" ) )
		self.assertNotEqual( a["out"]["globals"].hash(), a["in"]["globals"].hash() )
		self.assertEqual( a["out"]["globals"].getValue()["attribute:gaffer:transformBlurSegments"], IECore.IntData( 2 ) )

	def testPassThroughs( self ) :

		p = GafferScene.Plane()
		p["sets"].setValue( "flatThings" )

		a = GafferScene.StandardAttributes()
		a["in"].setInput( p["out"] )

		self.assertEqual( a["out"]["setNames"].hash(), p["out"]["setNames"].hash() )
		self.assertEqual( a["out"].setHash( "flatThings" ), p["out"].setHash( "flatThings" ) )
		self.assertTrue( a["out"].set( "flatThings", _copy=False ).isSame( p["out"].set( "flatThings", _copy=False ) ) )

	def assertPromotedAttribute( self, script ) :

		self.assertIn( "attributes_visibility", script["Box"] )
		self.assertIsInstance( script["Box"]["attributes_visibility"], Gaffer.NameValuePlug )

		self.assertIn( "name", script["Box"]["attributes_visibility"] )
		self.assertIsInstance( script["Box"]["attributes_visibility"]["name"], Gaffer.StringPlug )

		self.assertIn( "value", script["Box"]["attributes_visibility"] )
		self.assertIsInstance( script["Box"]["attributes_visibility"]["value"], Gaffer.BoolPlug )

		self.assertIn( "enabled", script["Box"]["attributes_visibility"] )
		self.assertIsInstance( script["Box"]["attributes_visibility"]["enabled"], Gaffer.BoolPlug )

		self.assertTrue( Gaffer.PlugAlgo.isPromoted( script["Box"]["StandardAttributes"]["attributes"]["visibility"] ) )
		self.assertEqual(
			script["Box"]["StandardAttributes"]["attributes"]["visibility"].getInput(),
			script["Box"]["attributes_visibility"]
		)

		self.assertTrue( script["Box"]["attributes_visibility"].getFlags( Gaffer.Plug.Flags.Dynamic ) )

	def testLoadPromotedAttributeFrom0_53( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "promotedCompoundDataMemberPlug-0.53.4.0.gfr" )
		s.load()
		self.assertPromotedAttribute( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertPromotedAttribute( s2 )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )
		self.assertPromotedAttribute( s3 )

	def testPromoteAndSerialiseAttribute( self ) :

		s = Gaffer.ScriptNode()
		s["Box"] = Gaffer.Box()
		s["Box"]["StandardAttributes"] = GafferScene.StandardAttributes()
		Gaffer.PlugAlgo.promote( s["Box"]["StandardAttributes"]["attributes"]["visibility"] )
		self.assertPromotedAttribute( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertPromotedAttribute( s2 )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )
		self.assertPromotedAttribute( s3 )

if __name__ == "__main__":
	unittest.main()
