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

import imath
import pathlib

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class StandardOptionsTest( GafferSceneTest.SceneTestCase ) :

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["r"] = GafferScene.StandardOptions()
		s["r"]["options"]["render:camera"]["value"].setValue( "/path/to/a/camera" )
		names = s["r"]["options"].keys()

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["r"]["options"].keys(), names )
		self.assertTrue( "options1" not in s2["r"] )
		self.assertEqual( s2["r"]["options"]["render:camera"]["value"].getValue(), "/path/to/a/camera" )

	def testResolution( self ) :

		o = GafferScene.StandardOptions()

		o["options"]["render:resolution"]["value"].setValue( imath.V2i( 10 ) )
		o["options"]["render:resolution"]["enabled"].setValue( True )
		self.assertEqual( o["out"]["globals"].getValue()["option:render:resolution"].value, imath.V2i( 10 ) )

		o["options"]["render:resolution"]["value"].setValue( imath.V2i( 20 ) )
		self.assertEqual( o["out"]["globals"].getValue()["option:render:resolution"].value, imath.V2i( 20 ) )

	def testHashIncludesInputHash( self ) :

		o1 = GafferScene.StandardOptions()
		o2 = GafferScene.StandardOptions()
		o2["in"].setInput( o1["out"] )

		h = o2["out"]["globals"].hash()

		o1["options"]["render:resolution"]["enabled"].setValue( True )
		o1["options"]["render:resolution"]["value"].setValue( imath.V2i( 10 ) )

		self.assertNotEqual( o2["out"]["globals"].hash(), h )

	def testBoxPromotion( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferScene.StandardOptions()
		s["n"]["options"]["render:camera"]["enabled"].setValue( True )
		s["n"]["options"]["render:camera"]["value"].setValue( "/group/camera" )

		memberDataAndName = s["n"]["options"].memberDataAndName( s["n"]["options"]["render:camera"] )

		Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		Gaffer.PlugAlgo.promote( s["Box"]["n"]["options"]["render:camera"] )

		self.assertEqual(
			s["Box"]["n"]["options"].memberDataAndName( s["Box"]["n"]["options"]["render:camera"] ),
			memberDataAndName,
		)

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual(
			s2["Box"]["n"]["options"].memberDataAndName( s2["Box"]["n"]["options"]["render:camera"] ),
			memberDataAndName
		)

	def testNoValuesEnabledByDefault( self ) :

		n = GafferScene.StandardOptions()
		for p in n["options"].children() :
			self.assertEqual( p["enabled"].getValue(), False )

	def testNodeConstructsWithAllOptions( self ) :

		node = GafferScene.StandardOptions()
		for option in Gaffer.Metadata.targetsWithMetadata( "option:render:* option:sampleMotion", "defaultValue" ) :
			option = option[7:]
			with self.subTest( option = option ) :
				self.assertIn( option, node["options"] )
				self.assertEqual( node["options"][option]["name"].getValue(), option )
				self.assertEqual(
					node["options"][option]["value"].defaultValue(),
					Gaffer.Metadata.value( f"option:{option}", "defaultValue" )
				)

	def testLoadFrom1_5( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "standardOptions-1.5.14.0.gfr" )
		script.load()

		self.assertIn( "render:camera", script["StandardOptions"]["options"] )
		self.assertNotIn( "renderCamera", script["StandardOptions"]["options"] )
		self.assertEqual( script["StandardOptions"]["options"]["render:camera"]["value"].getValue(), "test" )

if __name__ == "__main__":
	unittest.main()
