##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class GlobalsSanitiserTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane = GafferScene.Plane()

		attributeQuery = GafferScene.AttributeQuery()
		attributeQuery.setup( Gaffer.BoolPlug() )
		attributeQuery["scene"].setInput( plane["out"] )
		attributeQuery["location"].setValue( "/plane" )
		attributeQuery["attribute"].setValue( "test" )

		options1 = GafferScene.StandardOptions( "options1" )
		options1["options"]["render:camera"]["enabled"].setInput( attributeQuery["value"] )

		options2 = GafferScene.StandardOptions( "options2" )
		options2["in"].setInput( options1["out"] )

		# A GlobalsSanitiser is automatically hooked up by SceneTestCase.setUp, so
		# we don't need to explicitly set one up
		with IECore.CapturingMessageHandler() as mh :
			options2["out"].globals()

		for message in mh.messages :
			self.assertEqual( message.level, mh.Level.Warning )
			self.assertEqual( message.context, "GlobalsSanitiser" )

		self.assertEqual(
			[ m.message for m in mh.messages ],
			[
				"Globals options1.out.globals depends on Plane.out.exists",
				"Globals options1.out.globals depends on Plane.out.attributes",
			]
		)

if __name__ == "__main__":
	unittest.main()
