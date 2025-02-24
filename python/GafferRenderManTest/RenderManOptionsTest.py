##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import GafferSceneTest
import GafferRenderMan

class RenderManOptionsTest( GafferSceneTest.SceneTestCase ) :

	def testOptionMetadata( self ) :

		# Check a few of the registrations we expect from `startup/GafferScene/renderManOptions.py`.
		self.assertEqual( Gaffer.Metadata.value( "option:ri:hider:bakebboxmin", "label" ), "Baking bbox min" )
		# Yes, the double-namespacing of `ri:Ri` is absurd, but that's the logical consequence of adhering to the
		# RenderMan naming, and matches the `PxrOptionsAPI` USD schema.
		self.assertEqual( Gaffer.Metadata.value( "option:ri:Ri:PixelFilterName", "label" ), " Pixel Filter" )
		self.assertEqual( Gaffer.Metadata.value( "option:ri:hider:bakemode", "presetNames" ), IECore.StringVectorData( [ "Pattern", "Integrator", "All" ] ) )
		self.assertEqual( Gaffer.Metadata.value( "option:ri:hider:bakemode", "presetValues" ), IECore.StringVectorData( [ "pattern", "integrator", "all" ] ) )
		self.assertEqual( Gaffer.Metadata.value( "option:ri:hider:bakemode", "plugValueWidget:type" ), "GafferUI.PresetsPlugValueWidget" )
		self.assertEqual( Gaffer.Metadata.value( "option:ri:hider:adaptivemetric", "defaultValue" ), "variance" )
		self.assertEqual( Gaffer.Metadata.value( "option:ri:osl:verbose", "presetNames" ), IECore.StringVectorData( [ "0 - Silent", "1 - Severe", "2 - Error", "3 - Message", "4 - Warning", "5 - Info" ] ) )
		self.assertEqual( Gaffer.Metadata.value( "option:ri:osl:verbose", "presetValues" ), IECore.IntVectorData( [ 0, 1, 2, 3, 4, 5 ] ) )
		self.assertEqual( Gaffer.Metadata.value( "option:ri:shade:debug", "defaultValue" ), False )

	def testAllOptionMetadataHasDefaultValue( self ) :

		self.assertTrue(
			Gaffer.Metadata.targetsWithMetadata( "option:ri:*", "label" ),
		)

		self.assertEqual(
			Gaffer.Metadata.targetsWithMetadata( "option:ri:*", "label" ),
			Gaffer.Metadata.targetsWithMetadata( "option:ri:*", "defaultValue" ),
		)

	def testOmittedOptionMetadata( self ) :

		# We don't register these because we deal with them in a renderer-agnostic way, and we don't
		# want users to specify them directly.
		self.assertFalse( Gaffer.Metadata.registeredValues( "option:ri:Ri:Frame" ) )
		self.assertFalse( Gaffer.Metadata.registeredValues( "option:ri:Ri:FrameAspectRatio" ) )
		self.assertFalse( Gaffer.Metadata.registeredValues( "option:ri:Ri:ScreenWindow" ) )
		self.assertFalse( Gaffer.Metadata.registeredValues( "option:ri:Ri:CropWindow" ) )
		self.assertFalse( Gaffer.Metadata.registeredValues( "option:ri:Ri:FormatPixelAspectRatio" ) )
		self.assertFalse( Gaffer.Metadata.registeredValues( "option:ri:Ri:FormatResolution" ) )
		self.assertFalse( Gaffer.Metadata.registeredValues( "option:ri:Ri:Shutter" ) )
		# Check we're not leaking implementation details of the parser.
		self.assertIsNone( Gaffer.Metadata.value( "option:ri:hider:adaptivemetric", "__type" ) )

	def testOmittedPresets( self ) :

		adaptiveMetrics = Gaffer.Metadata.value( "option:ri:hider:adaptivemetric", "presetValues" )
		self.assertNotIn( "contrast-v22", adaptiveMetrics )
		self.assertNotIn( "variance-v22", adaptiveMetrics )

	def testNodeConstructsWithAllOptions( self ) :

		node = GafferRenderMan.RenderManOptions()
		for option in Gaffer.Metadata.targetsWithMetadata( "option:ri:*", "defaultValue" ) :
			option = option[7:]
			with self.subTest( option = option ) :
				self.assertIn( option, node["options"] )
				self.assertEqual( node["options"][option]["name"].getValue(), option )
				self.assertEqual(
					node["options"][option]["value"].defaultValue(),
					Gaffer.Metadata.value( f"option:{option}", "defaultValue" )
				)

if __name__ == "__main__":
	unittest.main()
