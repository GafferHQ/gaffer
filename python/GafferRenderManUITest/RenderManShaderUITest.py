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
from xml.etree import cElementTree

import IECore

import Gaffer
import GafferUITest

import GafferRenderMan
import GafferRenderManUI

class RenderManShaderUITest( GafferUITest.TestCase ) :

	def testArgFileMetadata( self ) :

		n = GafferRenderMan.RenderManShader()
		n.loadShader( "PxrSurface" )

		self.ignoreMessage( IECore.Msg.Level.Warning, "RenderManShader::loadShader", 'Array parameter "utilityPattern" not supported' )

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

			for event, element in cElementTree.iterparse( argsFile, events = ( "start", "end" ) ) :
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
					self.assertRegex( m.message, 'Spline parameter .* not supported|.* has unsupported type "bxdf|.* has unsupported type "struct"' )

				# Trigger metadata parsing and ensure there are no errors
				Gaffer.Metadata.value( node, "description" )

				shadersLoaded.add( argsFile.stem )

		# Guard against shaders being moved and this test therefore not
		# loading anything.
		self.assertIn( "PxrSurface", shadersLoaded )

if __name__ == "__main__":
	unittest.main()
