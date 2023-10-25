##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import GafferUI
import GafferUITest

class PythonEditorTest( GafferUITest.TestCase ) :

	def testLifetimeAfterExecute( self ) :

		script = Gaffer.ScriptNode()
		editor = GafferUI.PythonEditor( script )
		weakEditor = weakref.ref( editor )

		editor.inputWidget().setText( "a = 10" )
		editor.execute()

		del editor
		self.assertIsNone( weakEditor() )

	def testPrint( self ) :

		script = Gaffer.ScriptNode()
		editor = GafferUI.PythonEditor( script )
		weakEditor = weakref.ref( editor )

		editor.inputWidget().setText( "print( 1, 2 )" )
		editor.execute()
		self.assertEqual(
			editor.outputWidget().getText(),
			"print( 1, 2 )\n1 2"
		)

		del editor
		self.assertIsNone( weakEditor() )

	def testLifetimeAfterExecuteException( self ) :

		script = Gaffer.ScriptNode()
		editor = GafferUI.PythonEditor( script )
		weakEditor = weakref.ref( editor )

		editor.inputWidget().setText( "ohDearThisVariableDoesntExist" )
		editor.execute()
		self.assertIn( "name 'ohDearThisVariableDoesntExist' is not defined", editor.outputWidget().getText() )

		del editor
		self.assertIsNone( weakEditor() )

	def testMessageHandler( self ) :

		script = Gaffer.ScriptNode()
		editor = GafferUI.PythonEditor( script )
		weakEditor = weakref.ref( editor )

		editor.inputWidget().setText( 'import IECore; IECore.msg( IECore.Msg.Level.Warning, "PythonEditorTest", "Alert!" )' )
		editor.execute()

		output = editor.outputWidget().getText()
		self.assertIn( "import IECore", output )
		self.assertIn( "WARNING : PythonEditorTest", output )
		self.assertIn( "Alert!", output )

		del editor
		self.assertIsNone( weakEditor() )

if __name__ == "__main__":
	unittest.main()
