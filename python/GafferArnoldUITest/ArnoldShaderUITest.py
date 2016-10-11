##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import GafferUITest
import GafferArnold
import GafferArnoldUI

class ArnoldShaderUITest( GafferUITest.TestCase ) :

	def testMetadata( self ) :

		shader = GafferArnold.ArnoldShader()
		shader.loadShader( "noise" )

		self.assertEqual(
			Gaffer.Metadata.value( shader["parameters"]["octaves"], "nodule:type" ),
			""
		)

		self.assertEqual(
			Gaffer.Metadata.value( shader["parameters"]["amplitude"], "nodule:type" ),
			"GafferUI::StandardNodule"
		)

		self.assertEqual(
			Gaffer.Metadata.value( shader["parameters"]["octaves"], "plugValueWidget:type" ),
			None
		)

		self.assertEqual(
			Gaffer.Metadata.value( shader["parameters"]["coord_space"], "plugValueWidget:type" ),
			"GafferUI.PresetsPlugValueWidget"
		)

		self.assertEqual(
			Gaffer.Metadata.value( shader["parameters"]["coord_space"], "presetNames" ),
			IECore.StringVectorData( [ "world", "object", "Pref" ] ),
		)

		self.assertEqual(
			Gaffer.Metadata.value( shader["parameters"]["coord_space"], "presetValues" ),
			Gaffer.Metadata.value( shader["parameters"]["coord_space"], "presetNames" ),
		)

	def testLightMetadata( self ) :

		light = GafferArnold.ArnoldLight()
		with IECore.CapturingMessageHandler() as mh :
			light.loadShader( "skydome_light" )

		## \todo Here we're suppressing warnings about not being
		# able to create plugs for some parameters. In many cases
		# these are parameters like "matrix" and "time_samples"
		# that we don't actually want to represent anyway. We should
		# add a mechanism for ignoring irrelevant parameters (perhaps
		# using custom gaffer.something metadata in additional Arnold
		# .mtd files), and then remove this suppression.
		for message in mh.messages :
			self.assertEqual( message.level, mh.Level.Warning )
			self.assertTrue( "Unsupported parameter" in message.message )

		self.assertEqual(
			Gaffer.Metadata.value( light["parameters"]["cast_shadows"], "nodule:type" ),
			""
		)

		self.assertEqual(
			Gaffer.Metadata.value( light["parameters"]["color"], "nodule:type" ),
			"GafferUI::StandardNodule"
		)

		self.assertEqual(
			Gaffer.Metadata.value( light["parameters"]["format"], "plugValueWidget:type" ),
			"GafferUI.PresetsPlugValueWidget"
		)

		self.assertEqual(
			Gaffer.Metadata.value( light["parameters"]["format"], "presetNames" ),
			IECore.StringVectorData( [ "mirrored_ball", "angular", "latlong" ] ),
		)

		self.assertEqual(
			Gaffer.Metadata.value( light["parameters"]["format"], "presetValues" ),
			Gaffer.Metadata.value( light["parameters"]["format"], "presetNames" ),
		)

if __name__ == "__main__":
	unittest.main()
