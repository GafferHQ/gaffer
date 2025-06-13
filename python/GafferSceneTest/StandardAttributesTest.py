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

import imath
import pathlib

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class StandardAttributesTest( GafferSceneTest.SceneTestCase ) :

	def testDefaultValues( self ) :

		s = GafferScene.StandardAttributes()

		self.assertEqual( s["attributes"]["scene:visible"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["doubleSided"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["gaffer:transformBlur"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["gaffer:transformBlurSegments"]["value"].getValue(), 1 )
		self.assertEqual( s["attributes"]["gaffer:deformationBlur"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["gaffer:deformationBlurSegments"]["value"].getValue(), 1 )
		self.assertEqual( s["attributes"]["linkedLights"]["value"].getValue(), "defaultLights" )

		self.assertEqual( s["attributes"]["scene:visible"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["doubleSided"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["gaffer:transformBlur"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["gaffer:transformBlurSegments"]["value"].defaultValue(), 1 )
		self.assertEqual( s["attributes"]["gaffer:deformationBlur"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["gaffer:deformationBlurSegments"]["value"].defaultValue(), 1 )
		self.assertEqual( s["attributes"]["linkedLights"]["value"].defaultValue(), "defaultLights" )

	def testSerialisationWithInvisibility( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferScene.StandardAttributes()
		s["a"]["attributes"]["scene:visible"]["value"].setValue( False )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["a"]["attributes"]["scene:visible"]["value"].getValue(), False )
		self.assertEqual( s2["a"]["attributes"]["scene:visible"]["value"].defaultValue(), True )

	def testGlobal( self ) :

		p = GafferScene.Plane()
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		a = GafferScene.StandardAttributes()
		a["in"].setInput( p["out"] )
		a["filter"].setInput( f["out"] )
		a["attributes"]["gaffer:transformBlurSegments"]["enabled"].setValue( True )
		a["attributes"]["gaffer:transformBlurSegments"]["value"].setValue( 2 )

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

	def assertPromotedAttribute( self, script, plugName ) :

		self.assertIn( plugName, script["Box"] )
		self.assertIsInstance( script["Box"][plugName], Gaffer.NameValuePlug )

		self.assertIn( "name", script["Box"][plugName] )
		self.assertIsInstance( script["Box"][plugName]["name"], Gaffer.StringPlug )

		self.assertIn( "value", script["Box"][plugName] )
		self.assertIsInstance( script["Box"][plugName]["value"], Gaffer.BoolPlug )

		self.assertIn( "enabled", script["Box"][plugName] )
		self.assertIsInstance( script["Box"][plugName]["enabled"], Gaffer.BoolPlug )

		self.assertTrue( Gaffer.PlugAlgo.isPromoted( script["Box"]["StandardAttributes"]["attributes"]["scene:visible"] ) )
		self.assertEqual(
			script["Box"]["StandardAttributes"]["attributes"]["scene:visible"].getInput(),
			script["Box"][plugName]
		)

		self.assertTrue( script["Box"][plugName].getFlags( Gaffer.Plug.Flags.Dynamic ) )

	def testLoadPromotedAttributeFrom0_53( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "promotedCompoundDataMemberPlug-0.53.4.0.gfr" )
		s.load()
		self.assertPromotedAttribute( s, "attributes_visibility" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertPromotedAttribute( s2, "attributes_visibility" )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )
		self.assertPromotedAttribute( s3, "attributes_visibility" )

	def testPromoteAndSerialiseAttribute( self ) :

		s = Gaffer.ScriptNode()
		s["Box"] = Gaffer.Box()
		s["Box"]["StandardAttributes"] = GafferScene.StandardAttributes()
		Gaffer.PlugAlgo.promote( s["Box"]["StandardAttributes"]["attributes"]["scene:visible"] )
		self.assertPromotedAttribute( s, "attributes_scene:visible" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertPromotedAttribute( s2, "attributes_scene:visible" )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )
		self.assertPromotedAttribute( s3, "attributes_scene:visible" )

	def testNodeConstructsWithAllAttributes( self ) :

		targets = "attribute:scene:visible attribute:doubleSided attribute:render:* attribute:gaffer:* " \
			+ "attribute:linkedLights attribute:shadowedLights attribute:filteredLights"

		node = GafferScene.StandardAttributes()
		for attribute in Gaffer.Metadata.targetsWithMetadata( targets, "defaultValue" ) :
			attribute = attribute[10:]
			with self.subTest( attribute = attribute ) :
				self.assertIn( attribute, node["attributes"] )
				self.assertEqual( node["attributes"][attribute]["name"].getValue(), attribute )
				self.assertEqual(
					node["attributes"][attribute]["value"].defaultValue(),
					Gaffer.Metadata.value( f"attribute:{attribute}", "defaultValue" )
				)

	def testLoadFrom1_5( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "standardAttributes-1.5.14.0.gfr" )
		script.load()

		self.assertIn( "render:displayColor", script["StandardAttributes"]["attributes"] )
		self.assertNotIn( "displayColor", script["StandardAttributes"]["attributes"] )
		self.assertEqual( script["StandardAttributes"]["attributes"]["render:displayColor"]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )

if __name__ == "__main__":
	unittest.main()
