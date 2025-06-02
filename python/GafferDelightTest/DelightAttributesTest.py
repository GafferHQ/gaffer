##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
import GafferDelight

class DelightAttributesTest( GafferSceneTest.SceneTestCase ) :

	def testValidity( self ) :

		o = GafferDelight.DelightAttributes()

		o["out"].transform( "/" )
		self.assertIsInstance( o["out"].childNames( "/" ), IECore.InternedStringVectorData )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferDelight.DelightAttributes()
		s["a"]["attributes"]["dl:matte"]["value"].setValue( True )
		names = s["a"]["attributes"].keys()

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["a"]["attributes"].keys(), names )
		self.assertTrue( "attributes1" not in s2["a"] )
		self.assertEqual( s2["a"]["attributes"]["dl:matte"]["value"].getValue(), True )

	def testNodeConstructsWithAllAttributes( self ) :

		node = GafferDelight.DelightAttributes()
		for attribute in Gaffer.Metadata.targetsWithMetadata( "attribute:dl:*", "defaultValue" ) :
			attribute = attribute[10:]
			plugName = attribute.replace( ".", "_" )
			with self.subTest( attribute = attribute, plugName = plugName ) :
				self.assertIn( plugName, node["attributes"] )
				self.assertEqual( node["attributes"][plugName]["name"].getValue(), attribute )
				self.assertEqual(
					node["attributes"][plugName]["value"].defaultValue(),
					Gaffer.Metadata.value( f"attribute:{attribute}", "defaultValue" )
				)

	def testLoadFrom1_5( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "delightAttributes-1.5.14.0.gfr" )
		script.load()

		self.assertIn( "dl:matte", script["DelightAttributes"]["attributes"] )
		self.assertNotIn( "matte", script["DelightAttributes"]["attributes"] )
		self.assertEqual( script["DelightAttributes"]["attributes"]["dl:matte"]["value"].getValue(), True )

if __name__ == "__main__":
	unittest.main()
