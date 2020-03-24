##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import Gaffer
import GafferImage
import GafferUI
import GafferUITest

from GafferImageUI import CatalogueUI

import IECore

class CatalogueUITest( GafferUITest.TestCase ) :

	def testStandardColumns( self ) :

		self.assertTrue( "typeIcon" in CatalogueUI.registeredColumns() )
		self.assertTrue( "name" in CatalogueUI.registeredColumns() )

		c = GafferImage.Catalogue()
		self.assertEqual(
			Gaffer.Metadata.value( c["imageIndex"], "catalogue:columns" ),
			IECore.StringVectorData( [ "typeIcon", "name" ] )
		)

	def testBoxedCatalogue( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["c"] = GafferImage.Catalogue()

		# 'images' is required to for serialisation if the
		# catalogue is inside a reference/extension.
		Gaffer.PlugAlgo.promote( s["b"]["c"]["images"] )
		Gaffer.PlugAlgo.promote( s["b"]["c"]["imageIndex"] )

		sw = GafferUI.ScriptWindow.acquire( s )
		ne = GafferUI.NodeEditor.acquire( s["b"] )

	def testImageHeaderColumns( self ) :

		class MockImagePlug() :

			def __init__( self, metadata = {} ) :
				self.__metadata = metadata

			def metadata( self ) :
				return self.__metadata

			def mockNode( self ) :
				return { "out" : self }

		mockPlug = MockImagePlug( {
			"gaffer:context:shot" : "G100",
			"gaffer:context:sequence" : "G",
			"customHeaderA" : "A",
			"customHeaderB": "B"
		} )

		catalogue = mockPlug.mockNode()

		# Header value provider

		c = CatalogueUI.ImageMetadataColumn( "Custom A", "customHeaderA" )
		self.assertEqual( c.value( None, catalogue ), "A" )

		c = CatalogueUI.ImageMetadataColumn( "Custom C", "customHeaderC" )
		self.assertEqual( c.value( None, catalogue ), None )

		c = CatalogueUI.ImageMetadataColumn( "Custom A", [ "customHeaderA" ] )
		self.assertEqual( c.value( None, catalogue ), "A" )

		c = CatalogueUI.ImageMetadataColumn( "Custom A", "customHeaderA", "X" )
		self.assertEqual( c.value( None, catalogue ), "A" )

		c = CatalogueUI.ImageMetadataColumn( "Custom C", "customHeaderC", "C" )
		self.assertEqual( c.value( None, catalogue ), "C" )

		c = CatalogueUI.ImageMetadataColumn( "Custom", [ "customHeaderC", "customHeaderB", "customHeaderA" ] )
		self.assertEqual( c.value( None, catalogue ), "B" )

		c = CatalogueUI.ImageMetadataColumn( "Custom", [ "customHeaderC", "customHeaderD" ], "X"  )
		self.assertEqual( c.value( None, catalogue ), "X" )

		# Context value provider

		c = CatalogueUI.ContextVariableColumn( "Shot", "shot" )
		self.assertEqual( c.value( None, catalogue ), "G100" )

		c = CatalogueUI.ContextVariableColumn( "Layer", "layer" )
		self.assertEqual( c.value( None, catalogue ), None )

		c = CatalogueUI.ContextVariableColumn( "Shot", [ "shot" ] )
		self.assertEqual( c.value( None, catalogue ), "G100" )

		c = CatalogueUI.ContextVariableColumn( "Shot", "shot", "X" )
		self.assertEqual( c.value( None, catalogue ), "G100" )

		c = CatalogueUI.ContextVariableColumn( "Layer", "layer", "L" )
		self.assertEqual( c.value( None, catalogue ), "L" )

		c = CatalogueUI.ContextVariableColumn( "Layer", [ "layer", "shot", "sequence" ] )
		self.assertEqual( c.value( None, catalogue ), "G100" )

		c = CatalogueUI.ContextVariableColumn( "Layer", [ "subLayer", "layer" ], "X"  )
		self.assertEqual( c.value( None, catalogue ), "X" )

if __name__ == "__main__":
	unittest.main()

