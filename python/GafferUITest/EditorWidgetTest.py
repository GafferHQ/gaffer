##########################################################################
#  
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

class EditorWidgetTest( GafferUITest.TestCase ) :

	def testLifetime( self ) :

		scriptNode = Gaffer.ScriptNode()
		scriptNode["write"] = Gaffer.WriteNode()
		scriptNode.selection().add( scriptNode["write"] )
				
		for type in GafferUI.EditorWidget.types() :
			editor = GafferUI.EditorWidget.create( type, scriptNode )
			w = weakref.ref( editor )
			del editor
			self.assertEqual( w(), None )
		
		self.assertEqual( w(), None )
	
	def testContext( self ) :
	
		s = Gaffer.ScriptNode()
		c = Gaffer.Context()
		
		editor = GafferUI.Viewer( s )
	
		self.failUnless( editor.scriptNode().isSame( s ) )
		self.failUnless( editor.getContext().isSame( s.context() ) )
		
		editor.setContext( c )
		self.failUnless( editor.scriptNode().isSame( s ) )
		self.failUnless( editor.getContext().isSame( c ) )
	
	def testSerialisation( self ) :
	
		scriptNode = Gaffer.ScriptNode()
		
		layouts = GafferUI.Layouts.acquire( Gaffer.Application( "Layout tester" ) )
		for type in GafferUI.EditorWidget.types() :
			editor = GafferUI.EditorWidget.create( type, scriptNode )
			layouts.add( "testLayout", editor )
			editor2 = layouts.create( "testLayout", scriptNode )
			self.failUnless( editor2.scriptNode() is scriptNode )
			
if __name__ == "__main__":
	unittest.main()
	
