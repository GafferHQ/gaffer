##########################################################################
#
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import weakref

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class EditorTest( GafferUITest.TestCase ) :

	def testLifetime( self ) :

		application = Gaffer.Application( "Layout tester" )
		scriptNode = Gaffer.ScriptNode()
		application.root()["scripts"].addChild( scriptNode )

		scriptNode["random"] = Gaffer.Random()
		scriptNode.selection().add( scriptNode["random"] )

		for type in GafferUI.Editor.types() :
			editor = GafferUI.Editor.create( type, scriptNode )
			w = weakref.ref( editor )
			del editor
			self.assertEqual( w(), None )

		self.assertEqual( w(), None )

	def testContext( self ) :

		s = Gaffer.ScriptNode()
		c = Gaffer.Context()

		editor = GafferUI.Viewer( s )

		self.assertTrue( editor.scriptNode().isSame( s ) )
		self.assertTrue( editor.getContext().isSame( s.context() ) )

		editor.setContext( c )
		self.assertTrue( editor.scriptNode().isSame( s ) )
		self.assertTrue( editor.getContext().isSame( c ) )

	def testSerialisation( self ) :

		application = Gaffer.Application( "Layout tester" )
		scriptNode = Gaffer.ScriptNode()
		application.root()["scripts"].addChild( scriptNode )

		layouts = GafferUI.Layouts.acquire( application )
		for type in GafferUI.Editor.types() :
			editor = GafferUI.Editor.create( type, scriptNode )
			layouts.add( "testLayout", editor )
			editor2 = layouts.create( "testLayout", scriptNode )
			self.assertTrue( editor2.scriptNode() is scriptNode )

	def testInstanceCreatedSignal( self ) :

		editorsCreated = []
		def editorCreated( editor ) :
			editorsCreated.append( editor )
		editorCreatedConnection = GafferUI.Editor.instanceCreatedSignal().connect( editorCreated )

		pythonEditorsCreated = []
		def pythonEditorCreated( editor ) :
			pythonEditorsCreated.append( editor )
		pythonEditorCreatedConnection = GafferUI.PythonEditor.instanceCreatedSignal().connect( pythonEditorCreated )

		s = Gaffer.ScriptNode()

		e1 = GafferUI.NodeEditor( s )
		e2 = GafferUI.PythonEditor( s )
		e3 = GafferUI.NodeEditor( s )

		self.assertEqual( editorsCreated, [ e1, e2, e3 ] )
		self.assertEqual( pythonEditorsCreated, [ e2 ] )

if __name__ == "__main__":
	unittest.main()
