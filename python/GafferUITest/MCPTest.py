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

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

from Qt import QtGui

class MCPTest( GafferUITest.TestCase ) :

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testListTools( self ) :

		server = Gaffer.MCP.HTTPServer()
		client = GafferTest.MCPTest.TestClient( server.port() )

		response = client.request( { "jsonrpc" : "2.0", "id" : 1, "method" : "tools/list" } )
		self.assertIn( "captureEditor", [ t["name"] for t in response["body"]["result"]["tools"] ] )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testCaptureEditor( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = Gaffer.Node()

		server = Gaffer.MCP.HTTPServer()
		server.addTarget( Gaffer.MCP.Server.Target( script ) )
		client = GafferTest.MCPTest.TestClient( server.port() )

		# Tabbed together, so only the GraphEditor is visible.
		layout = GafferUI.CompoundEditor( script )
		graphEditor = GafferUI.GraphEditor( script )
		layout.addEditor( GafferUI.NodeEditor( script ) )
		layout.addEditor( graphEditor )

		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		scriptWindow.setLayout( layout )
		scriptWindow.setVisible( True )
		self.waitForIdle( 1000 )

		# Can grab the GraphEditor because it is visible.

		result = client.callTool( "captureEditor", { "editor" : "GraphEditor" } )
		self.assertNotIn( "isError", result )

		image = self.__decodeImage( result["content"][1] )
		self.assertEqual( image.size(), graphEditor._qtWidget().grab().size() )

		# But the NodeEditor is not visible, so can't be grabbed.

		result = client.callTool( "captureEditor", { "editor" : "NodeEditor" } )
		self.assertTrue( result["isError"] )
		self.assertEqual( result["content"][0]["text"], "The NodeEditor is not visible" )

		# And there is no Viewer, so that can't be grabbed either.

		result = client.callTool( "captureEditor", { "editor" : "Viewer" } )
		self.assertTrue( result["isError"] )
		self.assertEqual( result["content"][0]["text"], "There is no Viewer" )

		# And there's no such thing as the FooEditor.

		result = client.callTool( "captureEditor", { "editor" : "FooEditor" } )
		self.assertTrue( result["isError"] )
		self.assertTrue( result["content"][0]["text"].startswith( "FooEditor is not an editor type" ) )

	def __decodeImage( self, content ) :

		self.assertEqual( content["type"], "image" )
		self.assertEqual( content["mimeType"], "image/png" )

		data = base64.b64decode( content["data"] )
		self.assertTrue( data.startswith( b"\x89PNG" ) )

		image = QtGui.QImage()
		self.assertTrue( image.loadFromData( data, "PNG" ) )
		return image
