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

import pathlib

import IECore

import Gaffer
import GafferScene
import GafferSceneTest
import GafferArnold

class ArnoldAttributesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()

		a = GafferArnold.ArnoldAttributes()
		a["in"].setInput( p["out"] )

		aa = a["out"].attributes( "/plane" )
		self.assertEqual( len( aa ), 0 )

		a["attributes"]["ai:visibility:camera"]["enabled"].setValue( True )
		a["attributes"]["ai:visibility:camera"]["value"].setValue( False )

		aa = a["out"].attributes( "/plane" )
		self.assertEqual( aa, IECore.CompoundObject( { "ai:visibility:camera" : IECore.BoolData( False ) } ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferArnold.ArnoldAttributes()
		s["a"]["attributes"]["ai:visibility:camera"]["value"].setValue( False )
		names = s["a"]["attributes"].keys()

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["a"]["attributes"].keys(), names )
		self.assertTrue( "attributes1" not in s2["a"] )
		self.assertEqual( s2["a"]["attributes"]["ai:visibility:camera"]["value"].getValue(), False )

	def testLoadFrom1_5( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "arnoldAttributes-1.5.13.0.gfr" )
		script.load()

		self.assertIn( "ai:visibility:camera", script["ArnoldAttributes"]["attributes"].keys() )
		self.assertNotIn( "cameraVisibility", script["ArnoldAttributes"]["attributes"].keys() )
		self.assertEqual( script["ArnoldAttributes"]["attributes"]["ai:visibility:camera"]["value"].getValue(), False )

if __name__ == "__main__":
	unittest.main()
