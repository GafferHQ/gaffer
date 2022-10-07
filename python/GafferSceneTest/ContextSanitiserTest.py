##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

class ContextSanitiserTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "a" )

		# A ContextSanitiser is automatically hooked up by SceneTestCase.setUp, so
		# we don't need to explicitly set one up
		with IECore.CapturingMessageHandler() as mh :
			with Gaffer.Context() as c :

				c["scene:path"] = IECore.InternedStringVectorData( [ "plane" ] )
				c["scene:setName"] = IECore.InternedStringData( "a" )
				plane["out"]["globals"].getValue()

				plane["out"]["set"].getValue()

				plane["out"]["object"].getValue()

				c["scene:setName"] = IECore.IntData( 5 )

				with self.assertRaisesRegex( IECore.Exception, 'Context variable is not of type "InternedStringData"' ) :
					plane["out"]["object"].getValue()

		for message in mh.messages :
			self.assertEqual( message.level, mh.Level.Warning )
			self.assertEqual( message.context, "ContextSanitiser" )

		self.assertEqual(
			[ m.message for m in mh.messages ],
			[
				"scene:setName in context for Plane.out.globals computeNode:hash",
				"scene:path in context for Plane.out.globals computeNode:hash",
				"scene:path in context for Plane.out.set computeNode:hash",
				"scene:setName in context for Plane.out.object computeNode:hash",
			]
		)

if __name__ == "__main__":
	unittest.main()
