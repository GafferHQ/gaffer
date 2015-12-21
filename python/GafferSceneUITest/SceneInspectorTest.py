##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUITest
import GafferScene
import GafferSceneUI

class SceneInspectorTest( GafferUITest.TestCase ) :

	def testTarget( self ) :

		g = GafferScene.Grid()
		t = GafferSceneUI.SceneInspector.Target( g["out"], "/grid" )

		self.assertTrue( t.scene.isSame( g["out"] ) )
		self.assertEqual( t.path, "/grid" )

		p = GafferScene.Plane()

		# Targets are read only
		self.assertRaises( AttributeError, setattr, t, "scene", p["out"] )
		self.assertRaises( AttributeError, setattr, t, "path", "/plane" )

		# Targets cache their lookups
		self.assertTrue( t.attributes().isSame( t.attributes() ) )
		self.assertTrue( t.fullAttributes().isSame( t.fullAttributes() ) )
		self.assertTrue( t.object().isSame( t.object() ) )
		self.assertTrue( t.globals().isSame( t.globals() ) )

	def testTargetPathsAccessors( self ) :

		script = Gaffer.ScriptNode()

		inspector = GafferSceneUI.SceneInspector( script )
		self.assertEqual( inspector.getTargetPaths(), None )

		inspector.setTargetPaths( [ "/plane" ] )
		self.assertEqual( inspector.getTargetPaths(), [ "/plane" ] )

		self.assertRaises( Exception, inspector.setTargetPaths, [ "/too", "/many", "/paths" ] )

if __name__ == "__main__":
	unittest.main()
