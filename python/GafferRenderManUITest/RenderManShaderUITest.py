##########################################################################
#
#  Copyright (c) 2018, John Haddon. All rights reserved.
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

import os
import pathlib
import unittest
from xml.etree import ElementTree

import IECore

import Gaffer
import GafferOSL
import GafferOSLUI
import GafferUITest

import GafferRenderMan
import GafferRenderManUI

class RenderManShaderUITest( GafferUITest.TestCase ) :

	def testArgFileMetadata( self ) :

		n = GafferRenderMan.RenderManShader()
		n.loadShader( "PxrSurface" )

		self.assertEqual(
			Gaffer.Metadata.value( n["parameters"]["diffuseGain"], "layout:section" ),
			"Diffuse"
		)

		self.assertEqual(
			Gaffer.Metadata.value( n["parameters"]["diffuseExponent"], "layout:section" ),
			"Diffuse.Advanced"
		)

		self.assertEqual(
			Gaffer.Metadata.value( n["parameters"]["diffuseGain"], "label" ),
			"Gain"
		)

		self.assertEqual(
			Gaffer.Metadata.value( n["parameters"]["continuationRayMode"], "presetNames" ),
			IECore.StringVectorData( [ "Off", "Last Hit", "All Hits" ] )
		)

		self.assertEqual(
			Gaffer.Metadata.value( n["parameters"]["continuationRayMode"], "presetValues" ),
			IECore.IntVectorData( [ 0, 1, 2 ] )
		)

		n.loadShader( "PxrVisualizer" )
		self.assertIn( "A utility integrator to navigate and inspect large scenes interactively", Gaffer.Metadata.value( n, "description" ) )

	def testCustomMetadata( self ) :

		# Check that all the metadata registered by
		# `startup/GafferRenderManUI/shaderMetadata.py` refers to shaders and
		# parameters that actually exist.

		node = GafferRenderMan.RenderManShader()

		for key in [ "noduleLayout:visible", "userDefault" ] :
			targets = Gaffer.Metadata.targetsWithMetadata( "ri:surface:*", key )
			shaders = { t.split( ":" )[2] for t in targets }
			for shader in shaders :
				with self.subTest( shader = shader ) :
					node.loadShader( shader )
					for target in targets :
						_, _, s, parameter = target.split( ":" )
						if s == shader :
							self.assertIn( parameter, node["parameters"] )

	def testUtilityPatternNodule( self ) :

		node = GafferRenderMan.RenderManShader()
		node.loadShader( "PxrSurface" )
		self.assertEqual( Gaffer.Metadata.value( node["parameters"]["utilityPattern"], "nodule:type" ), "GafferUI::CompoundNodule" )

	def testLoadAllStandardShaders( self ) :

		def __shaderType( argsFile ) :

			for event, element in ElementTree.iterparse( argsFile, events = ( "start", "end" ) ) :
				if element.tag == "shaderType" and event == "end" :
					tag = element.find( "tag" )
					return tag.attrib.get( "value" ) if tag is not None else None

			return None

		shadersLoaded = set()
		argsDir = pathlib.Path( os.environ["RMANTREE"] ) / "lib" / "plugins" / "Args"
		for argsFile in argsDir.glob( "*.args" ) :

			if __shaderType( argsFile ) not in {
				"bxdf", "light", "lightfilter", "samplefilter", "displayfilter", "integrator", "pattern", "displacement"
			} :
				continue

			if argsFile.stem in {
				"PxrCombinerLightFilter", "PxrSampleFilterCombiner", "PxrDisplayFilterCombiner",
			} :
				# These have `lightfilter`, `samplefilter` and `displayfilter` inputs
				# that we don't yet load. But they're not user-facing anyway.
				continue

			with self.subTest( shader = argsFile.stem ) :

				node = GafferRenderMan.RenderManShader()
				with IECore.CapturingMessageHandler() as mh :
					node.loadShader( argsFile.stem )

				for m in mh.messages :
					## \todo Add support for these types.
					self.assertRegex( m.message, 'Spline parameter .* not supported|.* has unsupported type "struct"' )

				for parameter in node["parameters"] :
					description = Gaffer.Metadata.value( parameter, "description" )
					if description is not None :
						self.assertNotIn( "<help>", description )
						self.assertNotIn( "</help>", description )
						self.assertNotIn( "{}:".format( parameter.getName() ), description )
						self.assertEqual( description.count( "<p>" ), description.count( "</p>" ) )

					# Check that there are no errors or warnings when evaluating
					# conditional visibility.
					Gaffer.Metadata.value( parameter, "layout:activator" )
					Gaffer.Metadata.value( parameter, "layout:visibilityActivator" )

				shadersLoaded.add( argsFile.stem )

		# Guard against shaders being moved and this test therefore not
		# loading anything.
		self.assertIn( "PxrSurface", shadersLoaded )

	def testSpecificActivator( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrSurface" )

		self.assertEqual( Gaffer.Metadata.value( shader["parameters"]["diffuseExponent"], "layout:visibilityActivator" ), True )
		shader["parameters"]["diffuseRoughness"].setValue( 0.1 )
		self.assertEqual( Gaffer.Metadata.value( shader["parameters"]["diffuseExponent"], "layout:visibilityActivator" ), False )

		shader.loadShader( "LamaConductor" )
		self.assertEqual( Gaffer.Metadata.value( shader["parameters"]["fresnelMode"], "layout:activator" ), True )

		self.assertEqual( Gaffer.Metadata.value( shader["parameters"]["exteriorIOR"], "layout:activator" ), False )
		shader["parameters"]["overrideExteriorIOR"].setValue( True )
		self.assertEqual( Gaffer.Metadata.value( shader["parameters"]["exteriorIOR"], "layout:activator" ), True )

	def testAllOSLActivators( self ) :

		# Load every RenderMan OSL shader and check that there are no
		# errors or warnings when evaluating their conditional visibility.

		shaderDir = pathlib.Path( os.environ["RMANTREE"] ) / "lib" / "shaders"
		shadersLoaded = set()

		for osoFile in shaderDir.glob( "*.oso" ) :

			with self.subTest( shader = osoFile.stem ) :

				node = GafferOSL.OSLShader( osoFile.stem )
				node.loadShader( osoFile.stem )

				for parameter in node["parameters"] :
					Gaffer.Metadata.value( parameter, "layout:activator" )
					Gaffer.Metadata.value( parameter, "layout:visibilityActivator" )

				shadersLoaded.add( osoFile.stem )

		# Guard against shaders being moved and this test therefore not
		# loading anything.
		self.assertIn( "PxrHairColor", shadersLoaded )

	def testSpecificOSLActivators( self ) :

		shader = GafferOSL.OSLShader()
		shader.loadShader( "PxrHairColor" )

		self.assertEqual( Gaffer.Metadata.value( shader["parameters"]["melanin"], "layout:activator" ), True )

		self.assertEqual( Gaffer.Metadata.value( shader["parameters"]["melanin"], "layout:visibilityActivator" ), True )
		self.assertEqual( Gaffer.Metadata.value( shader["parameters"]["Color"], "layout:visibilityActivator" ), False )

		shader["parameters"]["mode"].setValue( 1 ) # Artistic
		self.assertEqual( Gaffer.Metadata.value( shader["parameters"]["melanin"], "layout:visibilityActivator" ), False )
		self.assertEqual( Gaffer.Metadata.value( shader["parameters"]["Color"], "layout:visibilityActivator" ), True )

if __name__ == "__main__":
	unittest.main()
