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

import os

import Gaffer
import GafferImage
import GafferUI
import GafferUITest

from GafferImageUI import CatalogueUI

import IECore

class CatalogueUITest( GafferUITest.TestCase ) :

	def tearDown( self ) :

		# Clear the file cache to prevent Windows from refusing to delete open files,
		# then reset it to the original value to allow caching within subsequent tests.
		fLimit = GafferImage.OpenImageIOReader.getOpenFilesLimit()
		GafferImage.OpenImageIOReader.setOpenFilesLimit( 0 )
		GafferImage.OpenImageIOReader.setOpenFilesLimit( fLimit )

		GafferUITest.TestCase.tearDown( self )

	def testStandardColumns( self ) :

		self.assertTrue( "Status" in CatalogueUI.registeredColumns() )
		self.assertTrue( "Name" in CatalogueUI.registeredColumns() )
		self.assertTrue( "Output Index" in CatalogueUI.registeredColumns() )

		c = GafferImage.Catalogue()
		self.assertEqual(
			Gaffer.Metadata.value( c["imageIndex"], "catalogue:columns" ),
			IECore.StringVectorData( [ "Status", "Output Index", "Name" ] )
		)

	def testBoxedCatalogue( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["c"] = GafferImage.Catalogue()

		# 'images' is required to for serialisation if the
		# catalogue is inside a reference/extension.
		Gaffer.PlugAlgo.promote( s["b"]["c"]["images"] )
		Gaffer.PlugAlgo.promote( s["b"]["c"]["imageIndex"] )

		# Test metadata reset data or missing due to earlier promotion
		Gaffer.Metadata.deregisterValue( s["b"]["imageIndex"], "catalogue:columns" )

		sw = GafferUI.ScriptWindow.acquire( s )
		ne = GafferUI.NodeEditor.acquire( s["b"] )

	def testInvalidColumns( self ) :

		# Check we don't abort - columns may have been removed
		# from config but still be referenced by plug metadata.

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Catalogue()

		Gaffer.Metadata.registerValue(
			s["c"]["imageIndex"], "catalogue:columns",
			IECore.StringVectorData( [ "Name", "Unknown" ] )
		)

		sw = GafferUI.ScriptWindow.acquire( s )

		with IECore.CapturingMessageHandler() as mh :
			ne = GafferUI.NodeEditor.acquire( s["c"] )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Error )
		self.assertTrue( "Unknown" in mh.messages[0].message )

	def testImageHeaderColumns( self ) :

		script = Gaffer.ScriptNode()

		script["constant"] = GafferImage.Constant()

		script["metadata"] = GafferImage.ImageMetadata()
		script["metadata"]["in"].setInput( script["constant"]["out"] )
		script["metadata"]["metadata"].addChild( Gaffer.NameValuePlug( "gaffer:context:shot", "G100" ) )
		script["metadata"]["metadata"].addChild( Gaffer.NameValuePlug( "gaffer:context:sequence", "G" ) )
		script["metadata"]["metadata"].addChild( Gaffer.NameValuePlug( "customHeaderA", "A" ) )
		script["metadata"]["metadata"].addChild( Gaffer.NameValuePlug( "customHeaderB", "B" ) )

		script["imageWriter"] = GafferImage.ImageWriter()
		script["imageWriter"]["in"].setInput( script["metadata"]["out"] )
		script["imageWriter"]["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
		script["imageWriter"]["task"].execute()

		script["catalogue"] = GafferImage.Catalogue()
		script["catalogue"]["images"].addChild( GafferImage.Catalogue.Image.load( script["imageWriter"]["fileName"].getValue() ) )

		from GafferImageUI.CatalogueUI import _ImagesPath
		path = _ImagesPath( script["catalogue"]["images"], "/test" )

		# Header value provider

		c = CatalogueUI.ImageMetadataColumn( "Custom A", "customHeaderA" )
		self.assertEqual( c.cellData( path, None ).value, "A" )

		c = CatalogueUI.ImageMetadataColumn( "Custom C", "customHeaderC" )
		self.assertEqual( c.cellData( path, None ).value, None )

		c = CatalogueUI.ImageMetadataColumn( "Custom A", [ "customHeaderA" ] )
		self.assertEqual( c.cellData( path, None ).value, "A" )

		c = CatalogueUI.ImageMetadataColumn( "Custom A", "customHeaderA", "X" )
		self.assertEqual( c.cellData( path, None ).value, "A" )

		c = CatalogueUI.ImageMetadataColumn( "Custom C", "customHeaderC", "C" )
		self.assertEqual( c.cellData( path, None ).value, "C" )

		c = CatalogueUI.ImageMetadataColumn( "Custom", [ "customHeaderC", "customHeaderB", "customHeaderA" ] )
		self.assertEqual( c.cellData( path, None ).value, "B" )

		c = CatalogueUI.ImageMetadataColumn( "Custom", [ "customHeaderC", "customHeaderD" ], "X"  )
		self.assertEqual( c.cellData( path, None ).value, "X" )

		# Context value provider

		c = CatalogueUI.ContextVariableColumn( "Shot", "shot" )
		self.assertEqual( c.cellData( path, None ).value, "G100" )

		c = CatalogueUI.ContextVariableColumn( "Layer", "layer" )
		self.assertEqual( c.cellData( path, None ).value, None )

		c = CatalogueUI.ContextVariableColumn( "Shot", [ "shot" ] )
		self.assertEqual( c.cellData( path, None ).value, "G100" )

		c = CatalogueUI.ContextVariableColumn( "Shot", "shot", "X" )
		self.assertEqual( c.cellData( path, None ).value, "G100" )

		c = CatalogueUI.ContextVariableColumn( "Layer", "layer", "L" )
		self.assertEqual( c.cellData( path, None ).value, "L" )

		c = CatalogueUI.ContextVariableColumn( "Layer", [ "layer", "shot", "sequence" ] )
		self.assertEqual( c.cellData( path, None ).value, "G100" )

		c = CatalogueUI.ContextVariableColumn( "Layer", [ "subLayer", "layer" ], "X"  )
		self.assertEqual( c.cellData( path, None ).value, "X" )

if __name__ == "__main__":
	unittest.main()
