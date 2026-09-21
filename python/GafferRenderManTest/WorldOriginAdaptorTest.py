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

import imath

import GafferScene
import GafferSceneTest
import GafferRenderMan

class WorldOriginAdaptorTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		cube = GafferScene.Cube()
		cube["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )

		camera = GafferScene.Camera()
		camera["transform"]["translate"].setValue( imath.V3f( 10, 20, 30 ) )

		group = GafferScene.Group()
		group["in"][0].setInput( cube["out"] )
		group["in"][1].setInput( camera["out"] )

		standardOptions = GafferScene.StandardOptions()
		standardOptions["in"].setInput( group["out"] )

		renderManOptions = GafferRenderMan.RenderManOptions()
		renderManOptions["in"].setInput( standardOptions["out"] )

		adaptor = GafferRenderMan._WorldOriginAdaptor()
		adaptor["in"].setInput( renderManOptions["out"] )

		# Default of `worldorigin == "world"`. No scene edits required.

		self.assertScenesEqual( adaptor["in"], adaptor["out"] )
		self.assertSceneHashesEqual( adaptor["in"], adaptor["out"] )

		# Switch to `worldorigin == "worldoffset"`. No scene edits required
		# because no offset specified yet.

		renderManOptions["options"]["ri:trace:worldorigin"]["enabled"].setValue( True )
		renderManOptions["options"]["ri:trace:worldorigin"]["value"].setValue( "worldoffset" )
		self.assertScenesEqual( adaptor["in"], adaptor["out"] )

		# Specify offset, and scene should be translated so that the offset is
		# at the origin.

		renderManOptions["options"]["ri:trace:worldoffset"]["enabled"].setValue( True )
		renderManOptions["options"]["ri:trace:worldoffset"]["value"].setValue( imath.V3f( 5, 7, 8 ) )

		self.assertEqual( adaptor["out"].fullTransform( "/group/cube" ).translation(), imath.V3f( -4, -5, -5 ) )
		self.assertEqual( adaptor["out"].fullTransform( "/group/camera" ).translation(), imath.V3f( 5, 13, 22 ) )
		self.assertEqual( adaptor["out"].globals()["option:ri:trace:worldoffset"].value, imath.V3f( 5, 7, 8 ) )

		# Switch to `worldorigin == "camera"`. Transforms not changed because we haven't specified
		# a render camera yet.

		renderManOptions["options"]["ri:trace:worldoffset"]["enabled"].setValue( False )
		renderManOptions["options"]["ri:trace:worldorigin"]["value"].setValue( "camera" )

		self.assertScenesEqual( adaptor["in"], adaptor["out"], checks = self.allSceneChecks - { "globals" } )
		self.assertEqual( adaptor["out"].globals()["option:ri:trace:worldoffset"].value, imath.V3f( 0 ) )

		# Specify a camera, and the whole scene should be translated to bring it back
		# to the origin. And `worldorigin` should have been authored to tell RenderMan
		# about it.

		standardOptions["options"]["render:camera"]["enabled"].setValue( True )
		standardOptions["options"]["render:camera"]["value"].setValue( "/group/camera" )

		self.assertEqual( adaptor["out"].fullTransform( "/group/cube" ).translation(), imath.V3f( -9, -18, -27 ) )
		self.assertEqual( adaptor["out"].fullTransform( "/group/camera" ).translation(), imath.V3f( 0, 0, 0 ) )
		self.assertEqual( adaptor["out"].globals()["option:ri:trace:worldoffset"].value, imath.V3f( 10, 20, 30 ) )

		# If `worldoffset` is also authored by the user, then that should be added to
		# the offset from the camera. Not sure why - the minimal RenderMan docs don't
		# imply that it should be, but that's what hdPrman does.

		renderManOptions["options"]["ri:trace:worldoffset"]["enabled"].setValue( True )
		renderManOptions["options"]["ri:trace:worldoffset"]["value"].setValue( imath.V3f( 1, 2, 3, ) )

		self.assertEqual( adaptor["out"].fullTransform( "/group/cube" ).translation(), imath.V3f( -10, -20, -30 ) )
		self.assertEqual( adaptor["out"].fullTransform( "/group/camera" ).translation(), imath.V3f( -1, -2, -3 ) )
		self.assertEqual( adaptor["out"].globals()["option:ri:trace:worldoffset"].value, imath.V3f( 11, 22, 33 ) )
