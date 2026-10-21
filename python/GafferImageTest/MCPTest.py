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

import base64
import unittest

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class MCPTest( GafferImageTest.ImageTestCase ) :

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testListTools( self ) :

		server = Gaffer.MCP.HTTPServer()
		client = GafferTest.MCPTest.TestClient( server.port() )

		response = client.request( { "jsonrpc" : "2.0", "id" : 1, "method" : "tools/list" } )
		self.assertIn( "captureImage", [ t["name"] for t in response["body"]["result"]["tools"] ] )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testCaptureImage( self ) :

		script = Gaffer.ScriptNode()
		script["checkerboard"] = GafferImage.Checkerboard()
		script["checkerboard"]["format"].setValue( GafferImage.Format( 200, 100, 2.0 ) )

		server = Gaffer.MCP.HTTPServer()
		server.addTarget( Gaffer.MCP.Server.Target( script ) )
		client = GafferTest.MCPTest.TestClient( server.port() )

		result = client.callTool( "captureImage", { "plug" : "checkerboard.out", "maxSize" : 100 } )
		self.assertNotIn( "isError", result )
		self.assertEqual( result["content"][0]["type"], "text" )
		self.assertEqual( result["content"][0]["text"], 'Captured "checkerboard.out" (400x100), returned at 100x25' )

		# Check that a capture correctly downsizes and manages the conversion from
		# non-square to square pixels.

		image = self.__makeImageReader( result["content"][1] )
		self.assertEqual( image["out"].format(), GafferImage.Format( 100, 25 ) )

		# Check the script wasn't modified.
		self.assertEqual( script.children( Gaffer.Node ), ( script["checkerboard"], ) )
		self.assertEqual( script["checkerboard"]["out"].outputs(), () )
		self.assertFalse( script.undoAvailable() )

		# Check that images smaller than `maxSize` aren't resized.
		script["checkerboard"]["format"].setValue( GafferImage.Format( 100, 100 ) )
		result = client.callTool( "captureImage", { "plug" : "checkerboard.out" } )
		image = self.__makeImageReader( result["content"][1] )
		image["refreshCount"].setValue( image["refreshCount"].getValue() + 1 )
		self.assertEqual( image["out"].format(), GafferImage.Format( 100, 100 ) )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testCaptureImageLayer( self ) :

		script = Gaffer.ScriptNode()
		script["checkerboard"] = GafferImage.Checkerboard()
		script["checkerboard"]["format"].setValue( GafferImage.Format( 100, 100 ) )
		script["checkerboard"]["layer"].setValue( "testLayer" )

		server = Gaffer.MCP.HTTPServer()
		server.addTarget( Gaffer.MCP.Server.Target( script ) )
		client = GafferTest.MCPTest.TestClient( server.port() )

		# Non-existent layer leads to an error.

		result = client.callTool( "captureImage", { "plug" : "checkerboard.out" } )
		self.assertTrue( result["isError"] )
		self.assertEqual( result["content"][0]["type"], "text" )
		self.assertEqual( result["content"][0]["text"], 'Layer "" does not exist. Available layers : "testLayer"' )

		# Specifying a layer let us capture that layer.

		result = client.callTool( "captureImage", { "plug" : "checkerboard.out", "layer" : "testLayer" } )
		self.assertNotIn( "isError", result )
		self.assertEqual( result["content"][0]["type"], "text" )
		self.assertEqual( result["content"][0]["text"], 'Captured "checkerboard.out" (100x100), returned at 100x100' )

		image = self.__makeImageReader( result["content"][1] )

		# Verify against a capture of the default layer.

		script["checkerboard"]["layer"].setValue( "" )
		result = client.callTool( "captureImage", { "plug" : "checkerboard.out" } )
		expectedImage = self.__makeImageReader( result["content"][1] )

		self.assertImagesEqual( image["out"], expectedImage["out"], metadataBlacklist = [ "filePath" ] )

	def __makeImageReader( self, content ) :

		index = getattr( self, "_lastReaderIndex", 0 ) + 1
		self._lastReaderIndex = index

		self.assertEqual( content["type"], "image" )
		self.assertEqual( content["mimeType"], "image/png" )

		file = self.temporaryDirectory() / f"toLoad{index}.png"
		file.write_bytes( base64.b64decode( content["data"] ) )

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( file )

		return imageReader

if __name__ == "__main__":
	unittest.main()
