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

import Gaffer
import GafferScene
import GafferUITest
import GafferSceneUI

class SelectionToolTest( GafferUITest.TestCase ) :

	def modifierFunction( scene, path ) :

		return path

	def testRegisterSelectMode( self ) :

		GafferSceneUI.SelectionTool.registerSelectMode( "testModifier", self.modifierFunction )
		GafferSceneUI.SelectionTool.registerSelectMode( "testModifier2", self.modifierFunction )

		modifiers = GafferSceneUI.SelectionTool.registeredSelectModes()
		self.assertEqual( len( modifiers ), 3 )

		self.assertEqual( modifiers, [ "/Standard", "testModifier", "testModifier2" ] )

	def testSyncSelectMode( self ) :

		GafferSceneUI.SelectionTool.registerSelectMode( "testModifier", self.modifierFunction )

		script = Gaffer.ScriptNode()
		script["cube"] = GafferScene.Cube()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["cube"]["out"] )

		tool1 = GafferSceneUI.TranslateTool( view )
		tool2 = GafferSceneUI.RotateTool( view )

		self.assertEqual( len( [ i for i in view["tools"].children() if isinstance( i, GafferSceneUI.SelectionTool ) ] ), 2 )

		tool1["selectMode"].setValue( "testModifier" )
		self.assertEqual( tool1["selectMode"].getValue(), "testModifier" )
		self.assertEqual( tool2["selectMode"].getValue(), "testModifier" )

		tool2["selectMode"].setValue( "/Standard" )
		self.assertEqual( tool1["selectMode"].getValue(), "/Standard" )
		self.assertEqual( tool2["selectMode"].getValue(), "/Standard" )

	def tearDown( self ) :

		GafferUITest.TestCase.tearDown( self )

		GafferSceneUI.SelectionTool.deregisterSelectMode( "testModifier" )
		GafferSceneUI.SelectionTool.deregisterSelectMode( "testModifier2" )


if __name__ == "__main__" :
	unittest.main()