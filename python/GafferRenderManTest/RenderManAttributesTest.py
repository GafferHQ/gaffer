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

class RenderManAttributesTest( GafferSceneTest.SceneTestCase ) :

	def testAttributeMetadata( self ) :

		# Check a few of the registrations we expect from `startup/GafferScene/renderManAttributes.py`.
		self.assertEqual( Gaffer.Metadata.value( "option:ri:hider:bakebboxmin", "label" ), "Baking bbox min" )
		# Yes, the double-namespacing of `ri:Ri` is absurd, but that's the logical consequence of adhering to the
		# RenderMan naming, and matches the `PxrAttributesAPI` USD schema.
		self.assertEqual( Gaffer.Metadata.value( "attribute:ri:Ri:Matte", "label" ), "Matte" )

	def testAllAttributeMetadataHasDefaultValue( self ) :

		self.assertTrue(
			Gaffer.Metadata.targetsWithMetadata( "attribute:ri:*", "label" ),
		)

		self.assertEqual(
			set( Gaffer.Metadata.targetsWithMetadata( "attribute:ri:*", "label" ) ),
			set( Gaffer.Metadata.targetsWithMetadata( "attribute:ri:*", "defaultValue" ) ),
		)

	def testOmittedAttributesMetadata( self ) :

		# We don't register these because we deal with them in a renderer-agnostic way, and we don't
		# want users to specify them directly.
		self.assertFalse( Gaffer.Metadata.registeredValues( "attribute:ri:Ri:Sides" ) )
		self.assertFalse( Gaffer.Metadata.registeredValues( "attribute:ri:lighting:mute" ) )

	def testNodeConstructsWithAllAttributes( self ) :

		node = GafferRenderMan.RenderManAttributes()
		for attribute in Gaffer.Metadata.targetsWithMetadata( "attribute:ri:*", "defaultValue" ) :
			attribute = attribute[10:]
			with self.subTest( attribute = attribute ) :
				self.assertIn( attribute, node["attributes"] )
				self.assertEqual( node["attributes"][attribute]["name"].getValue(), attribute )
				self.assertEqual(
					node["attributes"][attribute]["value"].defaultValue(),
					Gaffer.Metadata.value( f"attribute:{attribute}", "defaultValue" )
				)

if __name__ == "__main__":
	unittest.main()
